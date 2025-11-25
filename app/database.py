"""
Database operations using SQLite with aiosqlite
"""
import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional

DATABASE_PATH = Path("data/rss_aggregator.db")


async def init_db():
    """Initialize database with required tables"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feed_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                last_updated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feed_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER NOT NULL,
                guid TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT,
                description TEXT,
                pub_date TIMESTAMP,
                author TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feed_id) REFERENCES feed_sources(id) ON DELETE CASCADE,
                UNIQUE(feed_id, guid)
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_feed_items_feed_id ON feed_items(feed_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_feed_items_pub_date ON feed_items(pub_date)
        """)
        
        await db.commit()


async def add_feed_source(url: str, name: str) -> int:
    """Add a new feed source"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "INSERT OR IGNORE INTO feed_sources (url, name) VALUES (?, ?)",
            (url, name)
        )
        await db.commit()
        
        if cursor.lastrowid:
            return cursor.lastrowid
        
        # If already exists, get the ID
        cursor = await db.execute(
            "SELECT id FROM feed_sources WHERE url = ?", (url,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_all_feed_sources() -> list[dict]:
    """Get all feed sources with item counts"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT 
                fs.id, 
                fs.url, 
                fs.name, 
                fs.last_updated,
                fs.created_at,
                COUNT(fi.id) as item_count
            FROM feed_sources fs
            LEFT JOIN feed_items fi ON fs.id = fi.feed_id
            GROUP BY fs.id
            ORDER BY fs.created_at DESC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_feed_source_by_id(feed_id: int) -> Optional[dict]:
    """Get a single feed source by ID"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM feed_sources WHERE id = ?", (feed_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def delete_feed_source(feed_id: int):
    """Delete a feed source and all its items"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM feed_items WHERE feed_id = ?", (feed_id,))
        await db.execute("DELETE FROM feed_sources WHERE id = ?", (feed_id,))
        await db.commit()


async def add_feed_items(feed_id: int, items: list[dict], max_items: int = 30):
    """Add new items to a feed, maintaining max_items limit"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for item in items:
            await db.execute("""
                INSERT OR REPLACE INTO feed_items 
                (feed_id, guid, title, link, description, pub_date, author)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feed_id,
                item['guid'],
                item['title'],
                item['link'],
                item['description'],
                item['pub_date'],
                item['author']
            ))
        
        # Update last_updated timestamp
        await db.execute(
            "UPDATE feed_sources SET last_updated = ? WHERE id = ?",
            (datetime.now(), feed_id)
        )
        
        # Keep only the latest max_items
        await db.execute("""
            DELETE FROM feed_items 
            WHERE feed_id = ? AND id NOT IN (
                SELECT id FROM feed_items 
                WHERE feed_id = ? 
                ORDER BY pub_date DESC 
                LIMIT ?
            )
        """, (feed_id, feed_id, max_items))
        
        await db.commit()


async def get_feed_items(feed_id: int, limit: int = 30) -> list[dict]:
    """Get items from a specific feed"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM feed_items 
            WHERE feed_id = ? 
            ORDER BY pub_date DESC 
            LIMIT ?
        """, (feed_id, limit))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def cleanup_old_items(cutoff_date: datetime):
    """Remove items older than cutoff date"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "DELETE FROM feed_items WHERE pub_date < ?",
            (cutoff_date,)
        )
        await db.commit()


