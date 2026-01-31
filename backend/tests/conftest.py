"""
pytest 配置文件
"""
import pytest
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    from unittest.mock import AsyncMock, MagicMock

    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    return db


@pytest.fixture
def mock_downloader():
    """创建模拟下载器"""
    from unittest.mock import AsyncMock, MagicMock

    downloader = MagicMock()
    downloader.id = 1
    downloader.name = "Test Downloader"
    downloader.type = "qbittorrent"
    downloader.host = "localhost"
    downloader.port = 8080
    downloader.username = "admin"
    downloader.password = "admin"
    downloader.use_ssl = False
    downloader.enabled = True

    return downloader


@pytest.fixture
def mock_torrent():
    """创建模拟种子信息"""
    from app.services.downloader.base import TorrentInfo
    from datetime import datetime

    return TorrentInfo(
        hash="abc123def456",
        name="Test.Torrent.2024.1080p.BluRay",
        size=5368709120,  # 5 GB
        progress=1.0,
        status="seeding",
        uploaded=10737418240,  # 10 GB
        downloaded=5368709120,  # 5 GB
        ratio=2.0,
        upload_speed=1048576,  # 1 MB/s
        download_speed=0,
        seeders=15,
        leechers=3,
        seeds_connected=5,
        peers_connected=2,
        tracker="https://tracker.example.com/announce",
        tags=["movies", "1080p"],
        category="movies",
        save_path="/downloads/movies",
        added_time=datetime.now(),
        seeding_time=86400,  # 1 day
    )


@pytest.fixture
def mock_delete_rule():
    """创建模拟删种规则"""
    from unittest.mock import MagicMock

    rule = MagicMock()
    rule.id = 1
    rule.name = "Test Rule"
    rule.enabled = True
    rule.priority = 100
    rule.conditions = [
        {
            "field": "seeding_time",
            "operator": ">",
            "value": 86400,
            "unit": "seconds"
        },
        {
            "field": "ratio",
            "operator": ">=",
            "value": 2.0,
            "unit": ""
        }
    ]
    rule.condition_logic = "and"
    rule.delete_files = False
    rule.only_delete_torrent = True
    rule.force_report = True
    rule.pause = False
    rule.limit_speed = 0
    rule.downloader_ids = [1]
    rule.tracker_filter = ""
    rule.category_filter = ""
    rule.tag_filter = ""
    rule.duration_seconds = 0

    return rule


@pytest.fixture
def mock_rss_feed():
    """创建模拟 RSS 订阅"""
    from unittest.mock import MagicMock
    from datetime import datetime

    feed = MagicMock()
    feed.id = 1
    feed.name = "Test Feed"
    feed.url = "https://example.com/rss?passkey=abc123"
    feed.enabled = True
    feed.auto_download = True
    feed.only_free = True
    feed.skip_hr = True
    feed.min_size = 0
    feed.max_size = 107374182400  # 100 GB
    feed.min_seeders = 1
    feed.include_keywords = ""
    feed.exclude_keywords = ""
    feed.fetch_interval = 300
    feed.last_fetch = None
    feed.first_run_done = False
    feed.downloader_id = 1
    feed.category = "movies"
    feed.save_path = ""
    feed.use_cookie_for_free_check = False
    feed.cookie = ""

    return feed
