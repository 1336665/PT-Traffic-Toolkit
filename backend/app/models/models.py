from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
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
    categories = Column(Text, default="")  # Comma separated (for RSS filter)

    # qBittorrent settings for downloaded torrents
    qb_category = Column(String(100), default="")  # qBittorrent category to assign
    qb_tags = Column(String(255), default="")  # qBittorrent tags to assign (comma separated)
    qb_save_path = Column(String(500), default="")  # Custom save path (optional)

    last_fetch = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    downloader = relationship("Downloader", back_populates="rss_feeds")
    records = relationship("RssRecord", back_populates="feed")


class RssRecord(Base):
    __tablename__ = "rss_records"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("rss_feeds.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False, index=True)  # Added index for faster lookups
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

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_rss_records_feed_created', 'feed_id', 'created_at'),
        Index('ix_rss_records_downloaded_created', 'downloaded', 'created_at'),
        Index('ix_rss_records_feed_link', 'feed_id', 'link'),  # Added for faster duplicate checking
    )

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
    pause = Column(Boolean, default=False)
    only_delete_torrent = Column(Boolean, default=False)
    limit_speed = Column(Integer, default=0)  # bytes/s, 0 = disabled
    rule_type = Column(String(20), default="normal")  # normal/javascript
    code = Column(Text, default="")

    # Scope
    downloader_ids = Column(JSON, default=list)  # Empty = all downloaders
    tracker_filter = Column(String(255), default="")  # Tracker domain filter
    tag_filter = Column(String(255), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeleteRecord(Base):
    __tablename__ = "delete_records"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("delete_rules.id"), nullable=True, index=True)
    rule_name = Column(String(100), default="")
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True, index=True)
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
    deleted_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Composite index for time-based queries
    __table_args__ = (
        Index('ix_delete_records_deleted_at_downloader', 'deleted_at', 'downloader_id'),
    )


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

    # 下载限速开关（防止超速，参考 u2_magic.py limit_download_speed）
    # 将两次汇报间的平均速度限制到 50M/s 以下，防止完成时汇报超速
    limit_download_speed = Column(Boolean, default=False)
    # 汇报优化开关（参考 u2_magic.py optimize_announce_time）
    # 在合适的时间强制汇报来调整完成前最后一次汇报时间，最大化上传量
    optimize_announce = Column(Boolean, default=False)
    # ====== 精准汇报时间（参考 u2_magic.py peer list 规则）======
    peerlist_enabled = Column(Boolean, default=False)
    peerlist_url_template = Column(String(500), default="")
    peerlist_cookie = Column(Text, default="")
    tid_regex = Column(String(255), default="")
    # peerlist返回的时间类型：
    # "elapsed" - 已过时间（从上次汇报到现在），需要用间隔减去它得到剩余时间
    # "remaining" - 剩余时间（距离下次汇报），直接使用
    peerlist_time_mode = Column(String(20), default="elapsed")
    # 自定义汇报间隔（秒），如果设置则优先使用，用于计算剩余时间
    # 0 表示使用tracker返回的间隔
    custom_announce_interval = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SpeedLimitRecord(Base):
    __tablename__ = "speed_limit_records"

    id = Column(Integer, primary_key=True, index=True)
    tracker_domain = Column(String(255), default="", index=True)
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)
    current_speed = Column(Float, default=0)  # Bytes/s
    target_speed = Column(Float, default=0)
    limit_applied = Column(Float, default=0)
    phase = Column(String(50), default="")  # warmup/catch/steady/finish
    uploaded = Column(Float, default=0)  # Bytes uploaded this interval
    downloaded = Column(Float, default=0)  # Bytes downloaded this interval
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Composite index for time-based queries
    __table_args__ = (
        Index('ix_speed_limit_records_created_downloader', 'created_at', 'downloader_id'),
    )


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

    # Downloader (支持单选，保持向后兼容)
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)
    # 多下载器支持 (JSON数组格式，如 "[1,2,3]")
    downloader_ids = Column(Text, default="")

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
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=False, index=True)
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

    # Unique constraint to prevent duplicate cache entries
    __table_args__ = (
        UniqueConstraint('downloader_id', 'torrent_hash', name='uix_torrent_cache_downloader_hash'),
        Index('ix_torrent_cache_downloader_hash', 'downloader_id', 'torrent_hash'),
    )


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

    # Composite indexes for common filter queries
    __table_args__ = (
        Index('ix_log_records_timestamp_level', 'timestamp', 'level'),
        Index('ix_log_records_timestamp_module', 'timestamp', 'module'),
    )


class DailyTrafficBaseline(Base):
    """Daily traffic baseline for calculating today's upload/download"""
    __tablename__ = "daily_traffic_baselines"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=False)

    # Baseline values at day start
    baseline_uploaded = Column(Float, default=0)  # Total uploaded at day start
    baseline_downloaded = Column(Float, default=0)  # Total downloaded at day start

    # Latest recorded values (updated periodically)
    latest_uploaded = Column(Float, default=0)
    latest_downloaded = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('date', 'downloader_id', name='uix_daily_traffic_date_downloader'),
        Index('ix_daily_traffic_date', 'date'),
    )


class NetcupThrottleStatus(str, enum.Enum):
    NORMAL = "normal"
    THROTTLED = "throttled"
    UNKNOWN = "unknown"


class NetcupAccount(Base):
    """Netcup SCP account for API authentication"""
    __tablename__ = "netcup_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Display name
    enabled = Column(Boolean, default=True)

    # SCP API credentials
    loginname = Column(String(100), nullable=False)  # Customer ID / Login name
    password = Column(String(255), nullable=False)  # SCP password (NOT webservice password)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    servers = relationship("NetcupServer", back_populates="account")


class NetcupServer(Base):
    """Netcup server configuration for throttle monitoring"""
    __tablename__ = "netcup_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)

    # Account association (for SCP API)
    account_id = Column(Integer, ForeignKey("netcup_accounts.id"), nullable=True)

    # Server identification (from SCP API)
    server_id_scp = Column(Integer, nullable=True)  # Server ID from Netcup SCP
    ip_address = Column(String(100), nullable=False)

    # SSH connection (for qBittorrent control)
    ssh_port = Column(Integer, default=22)
    ssh_username = Column(String(100), default="root")
    ssh_password = Column(String(255), default="")
    ssh_key_path = Column(String(500), default="")

    # qBittorrent control
    qb_control_type = Column(String(20), default="systemd")  # systemd/docker
    qb_docker_container = Column(String(100), default="")
    qb_systemd_service = Column(String(100), default="qbittorrent-nox")

    # qBittorrent API (for cleaning torrents before stop)
    qb_url = Column(String(255), default="")
    qb_username = Column(String(100), default="")
    qb_password = Column(String(255), default="")
    qb_path_mapping = Column(Text, default="{}")  # JSON: {"container_path": "host_path"}
    qb_excluded_categories = Column(Text, default="[]")  # JSON array of categories to preserve

    # Downloader association (for auto control)
    downloader_id = Column(Integer, ForeignKey("downloaders.id"), nullable=True)

    # Whitelist mode (only monitor, no auto control)
    whitelist = Column(Boolean, default=False)

    # Current status
    current_status = Column(SQLEnum(NetcupThrottleStatus), default=NetcupThrottleStatus.UNKNOWN)
    status_since = Column(DateTime, nullable=True)
    last_check = Column(DateTime, nullable=True)

    # Throttle time tracking
    throttle_start_time = Column(DateTime, nullable=True)
    throttle_end_time = Column(DateTime, nullable=True)
    throttle_duration = Column(Integer, nullable=True)  # seconds

    # Traffic statistics (from SCP API)
    monthly_rx_gib = Column(Float, default=0)
    monthly_tx_gib = Column(Float, default=0)
    interface_speed_mbits = Column(Integer, default=0)
    server_status = Column(String(20), default="UNKNOWN")  # RUNNING, STOPPED, etc.
    service_running = Column(Boolean, default=False)

    # Today's statistics
    today_normal_seconds = Column(Integer, default=0)
    today_throttled_seconds = Column(Integer, default=0)
    today_upload = Column(Float, default=0)  # bytes
    today_download = Column(Float, default=0)  # bytes
    stats_date = Column(String(10), default="")  # YYYY-MM-DD

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    account = relationship("NetcupAccount", back_populates="servers")
    records = relationship("NetcupRecord", back_populates="server")


class NetcupRecord(Base):
    """Netcup throttle status history"""
    __tablename__ = "netcup_records"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("netcup_servers.id"), nullable=False, index=True)
    status = Column(SQLEnum(NetcupThrottleStatus), nullable=False)
    duration_seconds = Column(Integer, default=0)
    upload_speed = Column(Float, default=0)  # bytes/s
    download_speed = Column(Float, default=0)  # bytes/s
    share_ratio = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Composite indexes
    __table_args__ = (
        Index('ix_netcup_records_server_created', 'server_id', 'created_at'),
    )

    # Relationships
    server = relationship("NetcupServer", back_populates="records")


class NetcupConfig(Base):
    """Global Netcup monitor configuration"""
    __tablename__ = "netcup_config"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=False)

    # Check interval
    check_interval = Column(Integer, default=60)  # seconds
    retry_interval = Column(Integer, default=30)  # seconds on error

    # Auto control
    auto_control_enabled = Column(Boolean, default=True)

    # Notification
    telegram_enabled = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
