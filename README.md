# RSS Aggregator for VMix

🇺🇦 **Ukrainian** | [🇬🇧 English](#english)

---

## 🇺🇦 Українська

Локальний RSS-агрегатор, створений спеціально для **VMix** та інших програм, які не мають вбудованого обмеження кількості новин у RSS-стрічках.

### Проблема

VMix та деякі інші програми завантажують **всі** новини з RSS-стрічки, що може призвести до:
- Перевантаження інтерфейсу
- Повільної роботи
- Відображення застарілих новин

### Рішення

Цей агрегатор:
- ✂️ Обмежує до **30 новин** на стрічку
- 🔄 Автоматично оновлюється кожні **5 хвилин**
- 🗑️ Видаляє новини старші **7 днів**
- 📡 Працює як локальний RSS-сервер

### Можливості

- 📡 Агрегація кількох RSS-стрічок
- 📰 Автоматичне обмеження до 30 новин на стрічку
- 🔄 Автооновлення кожні 5 хвилин
- 🗑️ Автовидалення старих новин (старше 7 днів)
- 🌐 Власний RSS-сервер для VMix та інших програм
- 🎨 Сучасний веб-інтерфейс
- 🐳 Docker-підтримка

### Швидкий старт

#### Одна команда (Docker Hub)

```bash
docker run -d -p 5050:5050 -v rss_data:/app/data --name rss-aggregator 101bogdan/rss-aggregator-vmix
```

#### Або з docker-compose

```bash
docker-compose up -d
```

Відкрийте браузер: http://localhost:5050

#### RSS-ендпоінти для VMix

- **Всі стрічки:** `http://localhost:5050/rss/all`
- **Окрема стрічка:** `http://localhost:5050/rss/feed/{id}`

### Команди

```bash
# Запустити
docker-compose up -d

# Зупинити
docker-compose down

# Переглянути логи
docker-compose logs -f

# Перебудувати (після змін)
docker-compose up -d --build
```

### Локальний запуск (без Docker)

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 5050
```

---

## 🇬🇧 English <a name="english"></a>

Local RSS aggregator created specifically for **VMix** and other applications that don't have built-in RSS feed item limits.

### Problem

VMix and some other applications load **all** items from RSS feeds, which can cause:
- Interface overload
- Slow performance
- Display of outdated news

### Solution

This aggregator:
- ✂️ Limits to **30 items** per feed
- 🔄 Auto-updates every **5 minutes**
- 🗑️ Removes items older than **7 days**
- 📡 Works as a local RSS server

### Features

- 📡 Multiple RSS feed aggregation
- 📰 Automatic limit of 30 items per feed
- 🔄 Auto-refresh every 5 minutes
- 🗑️ Auto-cleanup of old items (older than 7 days)
- 🌐 Local RSS server for VMix and other apps
- 🎨 Modern web interface
- 🐳 Docker support

### Quick Start

#### One command (Docker Hub)

```bash
docker run -d -p 5050:5050 -v rss_data:/app/data --name rss-aggregator 101bogdan/rss-aggregator-vmix
```

#### Or with docker-compose

```bash
docker-compose up -d
```

Open browser: http://localhost:5050

#### RSS Endpoints for VMix

- **All feeds:** `http://localhost:5050/rss/all`
- **Single feed:** `http://localhost:5050/rss/feed/{id}`

### Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Rebuild (after changes)
docker-compose up -d --build
```

### Local Run (without Docker)

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 5050
```

---

## Project Structure

```
├── app/
│   ├── main.py          # FastAPI application
│   ├── database.py      # SQLite operations
│   ├── rss_generator.py # RSS XML generator
│   ├── templates/       # HTML templates
│   └── static/          # CSS & JS
├── data/                # SQLite database
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Security

- 🔒 Parameterized SQL queries (SQL Injection protection)
- 🚫 No authentication (designed for local use)
- 📁 Database stored locally in `data/`
- 🔐 For public access, use reverse proxy with HTTPS

## Tech Stack

- **Backend:** Python, FastAPI, SQLite
- **Frontend:** HTML, CSS, JavaScript
- **Scheduler:** APScheduler
- **Container:** Docker

## Keywords

`rss` `vmix` `rss-aggregator` `rss-feed` `news-aggregator` `fastapi` `python` `docker` `broadcast` `live-streaming` `video-production` `rss-proxy` `rss-cache` `rss-limit`

## License

MIT
