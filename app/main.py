"""
RSS Feed Aggregator - Main Application
Aggregates RSS feeds, keeps last 30 items, and serves as local RSS server
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

import feedparser
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.database import (
    init_db,
    add_feed_source,
    get_all_feed_sources,
    delete_feed_source,
    add_feed_items,
    get_feed_items,
    cleanup_old_items,
    get_feed_source_by_id,
)
from app.rss_generator import generate_rss_feed

MAX_ITEMS_PER_FEED = 30
CLEANUP_DAYS = 7
UPDATE_INTERVAL_MINUTES = 5  # Оновлення кожні 5 хвилин


class FeedSourceCreate(BaseModel):
    url: str
    name: Optional[str] = None


class FeedSourceResponse(BaseModel):
    id: int
    url: str
    name: str
    last_updated: Optional[datetime]
    item_count: int


scheduler = AsyncIOScheduler()


async def fetch_and_update_feed(feed_id: int, feed_url: str):
    """Fetch RSS feed and update database"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            content = response.text

        feed = feedparser.parse(content)
        
        if feed.bozo and not feed.entries:
            print(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
            return

        items = []
        for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            items.append({
                'guid': entry.get('id', entry.get('link', '')),
                'title': entry.get('title', 'Без заголовка'),
                'link': entry.get('link', ''),
                'description': entry.get('summary', entry.get('description', '')),
                'pub_date': pub_date or datetime.now(),
                'author': entry.get('author', ''),
            })

        if items:
            await add_feed_items(feed_id, items, MAX_ITEMS_PER_FEED)
            print(f"Updated feed {feed_url}: {len(items)} items")

    except Exception as e:
        print(f"Error fetching feed {feed_url}: {e}")


async def update_all_feeds():
    """Update all registered feeds"""
    feeds = await get_all_feed_sources()
    for feed in feeds:
        await fetch_and_update_feed(feed['id'], feed['url'])
    
    # Cleanup old items
    cutoff_date = datetime.now() - timedelta(days=CLEANUP_DAYS)
    await cleanup_old_items(cutoff_date)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Initial fetch
    await update_all_feeds()
    
    # Schedule periodic updates
    scheduler.add_job(
        update_all_feeds,
        'interval',
        minutes=UPDATE_INTERVAL_MINUTES,
        id='update_feeds'
    )
    scheduler.start()
    
    yield
    
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="RSS Aggregator",
    description="Local RSS feed aggregator with web interface",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ============ API Endpoints ============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main web interface"""
    feeds = await get_all_feed_sources()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "feeds": feeds
    })


@app.get("/api/feeds")
async def list_feeds():
    """List all feed sources"""
    feeds = await get_all_feed_sources()
    return {"feeds": feeds}


@app.post("/api/feeds")
async def create_feed(feed: FeedSourceCreate):
    """Add a new feed source"""
    # Validate feed URL by trying to parse it
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(feed.url)
            response.raise_for_status()
            parsed = feedparser.parse(response.text)
            
            if parsed.bozo and not parsed.entries:
                raise HTTPException(status_code=400, detail="Неправильний RSS формат")
            
            feed_name = feed.name or parsed.feed.get('title', 'Без назви')
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Помилка завантаження: {str(e)}")

    feed_id = await add_feed_source(feed.url, feed_name)
    
    # Fetch items immediately
    await fetch_and_update_feed(feed_id, feed.url)
    
    return {"id": feed_id, "name": feed_name, "url": feed.url}


@app.delete("/api/feeds/{feed_id}")
async def remove_feed(feed_id: int):
    """Remove a feed source"""
    await delete_feed_source(feed_id)
    return {"status": "deleted"}


@app.get("/api/feeds/{feed_id}/items")
async def get_items(feed_id: int, limit: int = 30):
    """Get items from a specific feed"""
    items = await get_feed_items(feed_id, limit)
    return {"items": items}


@app.post("/api/feeds/refresh")
async def refresh_feeds():
    """Manually trigger feed refresh"""
    await update_all_feeds()
    return {"status": "refreshed"}


# ============ RSS Server Endpoints ============

@app.get("/rss/all", response_class=Response)
async def get_combined_rss():
    """Get combined RSS feed of all sources"""
    feeds = await get_all_feed_sources()
    all_items = []
    
    for feed in feeds:
        items = await get_feed_items(feed['id'], MAX_ITEMS_PER_FEED)
        for item in items:
            item['source_name'] = feed['name']
        all_items.extend(items)
    
    # Sort by date and limit to 30
    all_items.sort(key=lambda x: x['pub_date'] or datetime.min, reverse=True)
    all_items = all_items[:MAX_ITEMS_PER_FEED]
    
    rss_content = generate_rss_feed(
        title="RSS Aggregator - All Feeds",
        link="http://localhost:5050/rss/all",
        description="Combined feed from all sources",
        items=all_items
    )
    
    return Response(
        content=rss_content.encode('utf-8'),
        media_type="application/rss+xml; charset=utf-8"
    )


@app.get("/rss/feed/{feed_id}", response_class=Response)
async def get_single_rss(feed_id: int):
    """Get RSS feed for a single source"""
    feed = await get_feed_source_by_id(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    items = await get_feed_items(feed_id, MAX_ITEMS_PER_FEED)
    
    rss_content = generate_rss_feed(
        title=f"RSS Aggregator - {feed['name']}",
        link=f"http://localhost:5050/rss/feed/{feed_id}",
        description=f"Cached feed: {feed['name']}",
        items=items
    )
    
    return Response(
        content=rss_content.encode('utf-8'),
        media_type="application/rss+xml; charset=utf-8"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5050)

