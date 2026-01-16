from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class DownloaderType(str, enum.Enum):
    QBITTORRENT = "qbittorrent"
    TRANSMISSION = "transmission"
    DELUGE = "deluge"


class TorrentStatus(str, enum.Enum):
    DOWNLOADING = "downloading"
    SEEDING = "seeding"
    PAUSED = "paused"
    CHECKING = "checking"
    ERROR = "error"
    QUEUED = "queued"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Downloader(Base):
    __tablename__ = "downloaders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(DownloaderType), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), default="")
    password = Column(String(255), default="")
    use_ssl = Column(Boolean, default=False)
    download_dir = Column(String(500), default="")

    # Features
    enabled = Column(Boolean, default=True)
    auto_report = Column(Boolean, default=True)  # Auto report after 5 min
    download_first_last = Column(Boolean, default=False)
    auto_delete = Column(Boolean, default=True)
    auto_speed_limit = Column(Boolean, default=False)

    # Limits
    max_upload_speed = Column(Integer, default=0)  # KB/s, 0 = unlimited
    max_download_speed = Column(Integer, default=0)  # KB/s
    max_active_downloads = Column(Integer, default=0)  # 0 = unlimited
    disk_space_warning = Column(Integer, default=10)  # GB
    max_connections = Column(Integer, default=0)  # 0 = unlimited

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rss_feeds = relationship("RssFeed", back_populates="downloader")


class RssFeed(Base):
    __tablename__ = "rss_feeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=False)
    enabled = Column(Boolean, default=True)
    first_run_done = Column(Boolean, default=False)  # First run only records

    # Downloader assignment
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)
    auto_assign = Column(Boolean, default=True)  # Auto assign by free space

    # Site info for free detection
    site_cookie = Column(Text, default="")
    site_domain = Column(String(255), default="")

    # Fetch settings
    fetch_interval = Column(Integer, default=300)  # seconds

    # Limits
    max_upload_speed = Column(Integer, default=0)  # Per torrent KB/s
    max_download_speed = Column(Integer, default=0)
    downloader_max_upload = Column(Integer, default=0)  # KB/s
    downloader_max_download = Column(Integer, default=0)  # KB/s
    max_download_tasks = Column(Integer, default=0)

    # Filters
    only_free = Column(Boolean, default=False)
    exclude_hr = Column(Boolean, default=False)
    min_size = Column(Float, default=0)  # GB
    max_size = Column(Float, default=0)  # GB, 0 = unlimited
    min_seeders = Column(Integer, default=0)
    max_seeders = Column(Integer, default=0)  # 0 = unlimited
    include_keywords = Column(Text, default="")  # Comma separated
    exclude_keywords = Column(Text, default="")
    categories = Column(Text, default="")  # Comma separated

    last_fetch = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    downloader = relationship("Downloader", back_populates="rss_feeds")
    records = relationship("RssRecord", back_populates="feed")


class RssRecord(Base):
    __tablename__ = "rss_records"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("rss_feeds.id"), nullable=False)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    torrent_hash = Column(String(100), default="")
    size = Column(Float, default=0)  # Bytes
    is_free = Column(Boolean, default=False)
    is_hr = Column(Boolean, default=False)
    seeders = Column(Integer, default=0)
    leechers = Column(Integer, default=0)

    downloaded = Column(Boolean, default=False)
    download_time = Column(DateTime, nullable=True)
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)
    skip_reason = Column(String(255), default="")  # Why skipped

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    feed = relationship("RssFeed", back_populates="records")


class DeleteRule(Base):
    __tablename__ = "delete_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher = higher priority

    # Conditions (JSON array)
    # Each condition: {"field": "...", "operator": "...", "value": ..., "unit": "..."}
    conditions = Column(JSON, default=list)
    condition_logic = Column(String(10), default="AND")  # AND / OR

    # Duration check
    duration_seconds = Column(Integer, default=0)  # Must match for X seconds

    # Actions
    delete_files = Column(Boolean, default=True)
    force_report = Column(Boolean, default=True)  # Report before delete
    max_delete_count = Column(Integer, default=0)  # Per run, 0 = unlimited

    # Scope
    downloader_ids = Column(JSON, default=list)  # Empty = all downloaders
    tracker_filter = Column(String(255), default="")  # Tracker domain filter
    tag_filter = Column(String(255), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeleteRecord(Base):
    __tablename__ = "delete_records"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("delete_rules.id"), nullable=True)
    rule_name = Column(String(100), default="")
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)
    downloader_name = Column(String(100), default="")

    torrent_hash = Column(String(100), nullable=False)
    torrent_name = Column(String(500), nullable=False)
    size = Column(Float, default=0)  # Bytes
    uploaded = Column(Float, default=0)  # Bytes
    downloaded = Column(Float, default=0)  # Bytes
    ratio = Column(Float, default=0)
    seeding_time = Column(Integer, default=0)  # Seconds
    tracker = Column(String(255), default="")

    files_deleted = Column(Boolean, default=True)
    reported = Column(Boolean, default=False)
    deleted_at = Column(DateTime, default=datetime.utcnow)


class SpeedLimitConfig(Base):
    __tablename__ = "speed_limit_config"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=False)

    # Target speed (in bytes/s)
    target_upload_speed = Column(Float, default=0)
    target_download_speed = Column(Float, default=0)

    # Safety margin (0-1)
    safety_margin = Column(Float, default=0.1)

    # PID parameters
    kp = Column(Float, default=0.6)
    ki = Column(Float, default=0.1)
    kd = Column(Float, default=0.05)

    # Report interval (seconds)
    report_interval = Column(Integer, default=300)

    # Telegram notification
    telegram_enabled = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpeedLimitSite(Base):
    __tablename__ = "speed_limit_sites"

    id = Column(Integer, primary_key=True, index=True)
    tracker_domain = Column(String(255), nullable=False, unique=True)
    enabled = Column(Boolean, default=True)

    target_upload_speed = Column(Float, default=0)  # Bytes/s
    target_download_speed = Column(Float, default=0)
    safety_margin = Column(Float, default=0.1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpeedLimitRecord(Base):
    __tablename__ = "speed_limit_records"

    id = Column(Integer, primary_key=True, index=True)
    tracker_domain = Column(String(255), default="")
    current_speed = Column(Float, default=0)  # Bytes/s
    target_speed = Column(Float, default=0)
    limit_applied = Column(Float, default=0)
    phase = Column(String(50), default="")  # warmup/catch/steady/finish
    created_at = Column(DateTime, default=datetime.utcnow)


class U2MagicConfig(Base):
    __tablename__ = "u2_magic_config"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=False)

    # Authentication
    cookie = Column(Text, default="")
    api_token = Column(String(255), default="")
    uid = Column(Integer, default=0)  # U2 用户ID

    # Directories
    backup_dir = Column(String(500), default="")
    watch_dir = Column(String(500), default="")

    # Fetch interval
    fetch_interval = Column(Integer, default=60)  # seconds

    # Filters
    max_seeders = Column(Integer, default=20)
    download_new = Column(Boolean, default=True)
    download_old = Column(Boolean, default=True)
    min_size = Column(Float, default=0)  # GB
    max_size = Column(Float, default=0)  # GB
    categories = Column(Text, default="")  # Comma separated

    # 新增字段 - 完整移植原脚本功能
    min_day = Column(Integer, default=7)  # 判断新旧种的天数
    download_non_free = Column(Boolean, default=False)  # 下载非Free种子
    magic_self = Column(Boolean, default=False)  # 下载给自己的魔法
    effective_delay = Column(Integer, default=60)  # 魔法生效延迟（秒）
    download_dead = Column(Boolean, default=False)  # 下载无人做种的旧种
    da_qiao = Column(Boolean, default=True)  # 搭桥功能
    min_add_interval = Column(Integer, default=0)  # 重复添加最小间隔（秒）
    name_filter = Column(Text, default="")  # 名称过滤关键词

    # Downloader
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class U2MagicRecord(Base):
    __tablename__ = "u2_magic_records"

    id = Column(Integer, primary_key=True, index=True)
    torrent_id = Column(String(50), nullable=False)
    torrent_name = Column(String(500), nullable=False)
    torrent_hash = Column(String(100), default="")

    magic_type = Column(String(50), default="")  # free/2x/2xfree etc
    magic_duration = Column(Integer, default=0)  # Hours
    seeders = Column(Integer, default=0)
    leechers = Column(Integer, default=0)
    size = Column(Float, default=0)  # Bytes

    downloaded = Column(Boolean, default=False)
    download_time = Column(DateTime, nullable=True)
    skip_reason = Column(String(255), default="")

    created_at = Column(DateTime, default=datetime.utcnow)


class TorrentCache(Base):
    """Cache for torrent information"""
    __tablename__ = "torrent_cache"

    id = Column(Integer, primary_key=True, index=True)
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=False)
    torrent_hash = Column(String(100), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    size = Column(Float, default=0)  # Bytes
    progress = Column(Float, default=0)  # 0-1
    status = Column(SQLEnum(TorrentStatus), default=TorrentStatus.DOWNLOADING)

    uploaded = Column(Float, default=0)
    downloaded = Column(Float, default=0)
    ratio = Column(Float, default=0)
    upload_speed = Column(Float, default=0)
    download_speed = Column(Float, default=0)

    seeders = Column(Integer, default=0)
    leechers = Column(Integer, default=0)
    seeds_connected = Column(Integer, default=0)
    peers_connected = Column(Integer, default=0)

    tracker = Column(String(255), default="")
    tags = Column(Text, default="")
    category = Column(String(100), default="")
    save_path = Column(String(500), default="")

    added_time = Column(DateTime, nullable=True)
    seeding_time = Column(Integer, default=0)  # Seconds

    # For duration check in delete rules
    condition_met_since = Column(DateTime, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogRecord(Base):
    """System log records"""
    __tablename__ = "log_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(SQLEnum(LogLevel), default=LogLevel.INFO, index=True)
    module = Column(String(100), default="system", index=True)
    message = Column(Text, nullable=False)
    details = Column(Text, default="")

    # Keep index for fast queries
    __table_args__ = (
        # Composite index for filtering
    )
