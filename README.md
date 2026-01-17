# PT Manager Pro

A full-featured Private Tracker (PT) management web application with RSS subscription, intelligent deletion rules, dynamic speed limiting, and U2 magic catching.

## Features

- **Dashboard**: Real-time speed monitoring, storage stats, activity timeline
- **Downloader Management**: Support for qBittorrent, Transmission, Deluge
- **RSS Selection Strategy**: Automated torrent downloading with filters
- **Deletion Rules**: Visual rule builder with multiple conditions
- **Dynamic Speed Limiting**: PID control with Kalman filtering
- **U2 Magic Catcher**: Automatic free torrent detection for U2

## Quick Start

### Using Docker (Recommended)

```bash
# Clone or download the project
git clone <repository-url>
cd pt-manager

# Run installation script
chmod +x install.sh
./install.sh
```

Access the application at `http://localhost:8080`

### Interactive Management Script

```bash
chmod +x pt-manager.sh
./pt-manager.sh
```

The script provides an interactive menu for install, start, stop, restart, update, status, and logs.

### Manual Installation

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | `change-this-in-production` |
| `DATABASE_URL` | Database connection URL | `sqlite+aiosqlite:///./data/pt_manager.db` |
| `DEBUG` | Debug mode | `false` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional) | - |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (optional) | - |

### First Time Setup

1. Open `http://localhost:8080` in your browser
2. Create an admin account
3. Add your first downloader (qBittorrent, Transmission, or Deluge)
4. Configure RSS feeds, deletion rules, or other features

## Features Detail

### Downloader Management

- Support for multiple downloaders
- Auto-report after 5 minutes
- First/last piece priority
- Disk space monitoring
- Connection limits

### RSS Selection Strategy

- Multiple RSS feed support
- Free torrent detection (with site cookie)
- HR torrent exclusion
- Size/seeder filters
- Keyword include/exclude
- Auto-assign to downloader with most free space
- First-run mode (record only, no download)

### Deletion Rules

Visual rule builder with conditions:
- Progress, seeding time, ratio
- Upload/download amount and speed
- Size, seeders, leechers
- Tracker, tags, status
- Duration requirement (X seconds before delete)
- Force report before delete
- Preserve or delete files

### Dynamic Speed Limiting

- PID controller for precise speed control
- Kalman filter for speed prediction
- Multi-window speed tracking
- Per-site rules support
- Phases: warmup, catch, steady, finish

### U2 Magic Catcher

- Automatic free torrent detection
- Seeder limit filter
- Size filters
- New/old torrent preference
- Category filter
- Backup directory support

## API Documentation

API documentation is available at `http://localhost:8000/docs` when the backend is running.

## Tech Stack

### Backend
- FastAPI (Python 3.10+)
- SQLAlchemy 2.0 + SQLite
- APScheduler
- httpx, qbittorrent-api, transmission-rpc, deluge-client

### Frontend
- Vue 3 + Vite
- Tailwind CSS + Headless UI
- ECharts
- Pinia + Vue Router

## License

MIT License
