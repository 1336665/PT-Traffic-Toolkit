from datetime import datetime
from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, Field, field_validator
from app.models.models import DownloaderType, TorrentStatus


# ============ Generic Pagination Schema ============

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


# ============ Auth Schemas ============

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    """Request body for changing password - never send passwords via query params"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)


# ============ Downloader Schemas ============

class DownloaderBase(BaseModel):
    name: str
    type: DownloaderType
    host: str
    port: int
    username: str = ""
    password: str = ""
    use_ssl: bool = False
    download_dir: str = ""
    enabled: bool = True
    auto_report: bool = True
    download_first_last: bool = False
    auto_delete: bool = True
    auto_speed_limit: bool = False
    max_upload_speed: int = 0
    max_download_speed: int = 0
    max_active_downloads: int = 0
    disk_space_warning: int = 10
    max_connections: int = 0


class DownloaderCreate(DownloaderBase):
    pass


class DownloaderUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    use_ssl: Optional[bool] = None
    download_dir: Optional[str] = None
    enabled: Optional[bool] = None
    auto_report: Optional[bool] = None
    download_first_last: Optional[bool] = None
    auto_delete: Optional[bool] = None
    auto_speed_limit: Optional[bool] = None
    max_upload_speed: Optional[int] = None
    max_download_speed: Optional[int] = None
    max_active_downloads: Optional[int] = None
    disk_space_warning: Optional[int] = None
    max_connections: Optional[int] = None


class DownloaderResponse(DownloaderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DownloaderStatus(BaseModel):
    id: int
    name: str
    online: bool
    upload_speed: float = 0
    download_speed: float = 0
    free_space: float = 0
    active_torrents: int = 0
    total_torrents: int = 0
    seeding_torrents: int = 0
    downloading_torrents: int = 0
    total_uploaded: float = 0
    total_downloaded: float = 0


# ============ RSS Schemas ============

class RssFeedBase(BaseModel):
    name: str
    url: str
    enabled: bool = True
    downloader_id: Optional[int] = None
    auto_assign: bool = True
    site_cookie: str = ""
    site_domain: str = ""
    fetch_interval: int = 300
    max_upload_speed: int = 0
    max_download_speed: int = 0
    downloader_max_upload: int = 0
    downloader_max_download: int = 0
    max_download_tasks: int = 0
    only_free: bool = False
    exclude_hr: bool = False
    min_size: float = 0
    max_size: float = 0
    min_seeders: int = 0
    max_seeders: int = 0
    include_keywords: str = ""
    exclude_keywords: str = ""
    categories: str = ""
    qb_category: str = ""
    qb_tags: str = ""
    qb_save_path: str = ""


class RssFeedCreate(RssFeedBase):
    pass


class RssFeedUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    downloader_id: Optional[int] = None
    auto_assign: Optional[bool] = None
    site_cookie: Optional[str] = None
    site_domain: Optional[str] = None
    fetch_interval: Optional[int] = None
    max_upload_speed: Optional[int] = None
    max_download_speed: Optional[int] = None
    downloader_max_upload: Optional[int] = None
    downloader_max_download: Optional[int] = None
    max_download_tasks: Optional[int] = None
    only_free: Optional[bool] = None
    exclude_hr: Optional[bool] = None
    min_size: Optional[float] = None
    max_size: Optional[float] = None
    min_seeders: Optional[int] = None
    max_seeders: Optional[int] = None
    include_keywords: Optional[str] = None
    exclude_keywords: Optional[str] = None
    categories: Optional[str] = None
    qb_category: Optional[str] = None
    qb_tags: Optional[str] = None
    qb_save_path: Optional[str] = None


class RssFeedResponse(RssFeedBase):
    id: int
    first_run_done: bool
    last_fetch: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RssRecordResponse(BaseModel):
    id: int
    feed_id: int
    title: str
    link: str
    torrent_hash: str
    size: float
    is_free: bool
    is_hr: bool
    seeders: int
    leechers: int
    downloaded: bool
    download_time: Optional[datetime]
    skip_reason: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Delete Rule Schemas ============

class DeleteCondition(BaseModel):
    field: str  # progress, seeding_time, uploaded, downloaded, ratio, etc.
    operator: str  # gt, lt, eq, gte, lte, contains, not_contains
    value: Any
    unit: str = ""  # seconds, minutes, hours, days, MB, GB, KB/s, MB/s
    duration: int = 0  # Duration the condition must be met
    duration_unit: str = "seconds"  # seconds, minutes, hours, days


class DeleteRuleBase(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 0
    conditions: List[DeleteCondition] = []
    condition_logic: str = "AND"
    duration_seconds: int = 0
    delete_files: bool = True
    force_report: bool = True
    max_delete_count: int = 0
    pause: bool = False
    only_delete_torrent: bool = False
    limit_speed: int = 0
    rule_type: str = "normal"
    code: str = ""
    downloader_ids: List[int] = []
    tracker_filter: str = ""
    tag_filter: str = ""


class DeleteRuleCreate(DeleteRuleBase):
    pass


class DeleteRuleUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    conditions: Optional[List[DeleteCondition]] = None
    condition_logic: Optional[str] = None
    duration_seconds: Optional[int] = None
    delete_files: Optional[bool] = None
    force_report: Optional[bool] = None
    max_delete_count: Optional[int] = None
    pause: Optional[bool] = None
    only_delete_torrent: Optional[bool] = None
    limit_speed: Optional[int] = None
    rule_type: Optional[str] = None
    code: Optional[str] = None
    downloader_ids: Optional[List[int]] = None
    tracker_filter: Optional[str] = None
    tag_filter: Optional[str] = None


class DeleteRuleResponse(DeleteRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeleteRecordResponse(BaseModel):
    id: int
    rule_id: Optional[int]
    rule_name: str
    downloader_id: Optional[int]
    downloader_name: str
    torrent_hash: str
    torrent_name: str
    size: float
    uploaded: float
    downloaded: float
    ratio: float
    seeding_time: int
    tracker: str
    files_deleted: bool
    reported: bool
    action_type: str
    deleted_at: datetime

    class Config:
        from_attributes = True


# ============ Speed Limit Schemas ============

class SpeedLimitConfigBase(BaseModel):
    enabled: bool = False
    target_upload_speed: float = 0
    target_download_speed: float = 0
    safety_margin: float = 0.1
    kp: float = 0.6
    ki: float = 0.1
    kd: float = 0.05
    report_interval: int = 300
    telegram_enabled: bool = False

    @field_validator('target_upload_speed', 'target_download_speed')
    @classmethod
    def validate_speed(cls, v: float) -> float:
        if v < 0:
            raise ValueError('速度不能为负数')
        if v > 1000000000:  # 1GB/s
            raise ValueError('速度设置过大')
        return v

    @field_validator('safety_margin')
    @classmethod
    def validate_safety_margin(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError('安全余量必须在 0-1 之间')
        return v

    @field_validator('kp', 'ki', 'kd')
    @classmethod
    def validate_pid_params(cls, v: float) -> float:
        if v < 0 or v > 10:
            raise ValueError('PID 参数必须在 0-10 之间')
        return v

    @field_validator('report_interval')
    @classmethod
    def validate_report_interval(cls, v: int) -> int:
        if v < 60:
            raise ValueError('汇报间隔不能小于 60 秒')
        if v > 86400:
            raise ValueError('汇报间隔不能大于 24 小时')
        return v


class SpeedLimitConfigUpdate(SpeedLimitConfigBase):
    pass


class SpeedLimitConfigResponse(SpeedLimitConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class SpeedLimitSiteBase(BaseModel):
    tracker_domain: str
    enabled: bool = True
    target_upload_speed: float = 0
    target_download_speed: float = 0
    safety_margin: float = 0.1
    # 下载限速开关（防止超速）
    limit_download_speed: bool = False
    # 汇报优化开关
    optimize_announce: bool = False
    # 精准汇报时间（peer list）
    peerlist_enabled: bool = False
    peerlist_url_template: str = ""
    peerlist_cookie: str = ""
    tid_regex: str = ""
    # peerlist时间模式: "elapsed"=已过时间, "remaining"=剩余时间
    peerlist_time_mode: str = "elapsed"
    # 自定义汇报间隔（秒），0表示使用tracker返回的间隔
    custom_announce_interval: int = 0


class SpeedLimitSiteCreate(SpeedLimitSiteBase):
    pass


class SpeedLimitSiteUpdate(BaseModel):
    enabled: Optional[bool] = None
    target_upload_speed: Optional[float] = None
    target_download_speed: Optional[float] = None
    safety_margin: Optional[float] = None
    limit_download_speed: Optional[bool] = None
    optimize_announce: Optional[bool] = None
    peerlist_enabled: Optional[bool] = None
    peerlist_url_template: Optional[str] = None
    peerlist_cookie: Optional[str] = None
    tid_regex: Optional[str] = None
    peerlist_time_mode: Optional[str] = None
    custom_announce_interval: Optional[int] = None


class SpeedLimitSiteResponse(SpeedLimitSiteBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpeedLimitRecordResponse(BaseModel):
    id: int
    tracker_domain: str
    current_speed: float
    target_speed: float
    limit_applied: float
    phase: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ U2 Magic Schemas ============

class U2MagicConfigBase(BaseModel):
    enabled: bool = False
    cookie: str = ""
    api_token: str = ""
    uid: int = 0
    backup_dir: str = ""
    watch_dir: str = ""
    fetch_interval: int = 60
    max_seeders: int = 20
    download_new: bool = True
    download_old: bool = True
    min_size: float = 0
    max_size: float = 0
    categories: str = ""
    min_day: int = 7
    download_non_free: bool = False
    magic_self: bool = False
    effective_delay: int = 60
    download_dead: bool = False
    da_qiao: bool = True
    min_add_interval: int = 0
    name_filter: str = ""
    downloader_id: Optional[int] = None
    downloader_ids: str = ""  # JSON数组格式，如 "[1,2,3]"，支持多选下载器


class U2MagicConfigUpdate(U2MagicConfigBase):
    pass


class U2MagicConfigResponse(U2MagicConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class U2MagicRecordResponse(BaseModel):
    id: int
    torrent_id: str
    torrent_name: str
    torrent_hash: str
    magic_type: str
    magic_duration: int
    seeders: int
    leechers: int
    size: float
    downloaded: bool
    download_time: Optional[datetime]
    skip_reason: str
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Torrent Schemas ============

class TorrentInfo(BaseModel):
    hash: str
    name: str
    size: float
    progress: float
    status: str
    uploaded: float
    downloaded: float
    ratio: float
    upload_speed: float
    download_speed: float
    seeders: int
    leechers: int
    seeds_connected: int
    peers_connected: int
    tracker: str
    tags: str
    category: str
    save_path: str
    added_time: Optional[datetime]
    seeding_time: int
    total_size: Optional[float] = None
    selected_size: Optional[float] = None
    completed: Optional[float] = None
    completed_time: Optional[datetime] = None
    state: Optional[str] = None
    tracker_status: Optional[str] = ""


# ============ Dashboard Schemas ============

class DashboardStats(BaseModel):
    total_upload_speed: float
    total_download_speed: float
    total_uploaded: float
    total_downloaded: float
    active_torrents: int
    seeding_torrents: int
    downloading_torrents: int
    total_torrents: int
    total_size: float
    free_space: float


class TimelineItem(BaseModel):
    id: int
    type: str  # rss, delete, magic
    title: str
    description: str
    timestamp: datetime


# ============ System Schemas ============

class SystemStatus(BaseModel):
    initialized: bool
    version: str = "1.0.0"


# ============ Notification Schemas ============

class TelegramSettings(BaseModel):
    bot_token: str = ""
    chat_id: str = ""
    enabled: bool = False


class TelegramSettingsUpdate(BaseModel):
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    enabled: Optional[bool] = None


class TelegramTestResult(BaseModel):
    success: bool
    message: str


class NotificationSettings(BaseModel):
    telegram: TelegramSettings
    notify_rss_download: bool = True
    notify_delete: bool = True
    notify_speed_limit: bool = True
    notify_error: bool = True
    notify_low_disk: bool = True


# ============ Webhook Schemas ============

class WebhookEndpointBase(BaseModel):
    name: str
    url: str
    enabled: bool = True
    events: List[str] = []
    secret: str = ""


class WebhookEndpointCreate(WebhookEndpointBase):
    pass


class WebhookEndpointUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None


class WebhookEndpointResponse(WebhookEndpointBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Traffic Budget Schemas ============

class TrafficBudgetConfigBase(BaseModel):
    enabled: bool = False
    monthly_quota_gb: float = 0
    reset_day: int = 1
    warning_threshold: float = 0.8
    hard_limit: bool = False
    enforce_limits: bool = False
    downloader_type: str = "qbittorrent"
    max_upload_limit_kbps: int = 0


class TrafficBudgetConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    monthly_quota_gb: Optional[float] = None
    reset_day: Optional[int] = None
    warning_threshold: Optional[float] = None
    hard_limit: Optional[bool] = None
    enforce_limits: Optional[bool] = None
    downloader_type: Optional[str] = None
    max_upload_limit_kbps: Optional[int] = None


class TrafficBudgetConfigResponse(TrafficBudgetConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrafficBudgetStatus(BaseModel):
    period_start: datetime
    period_end: datetime
    uploaded_gb: float
    downloaded_gb: float
    total_gb: float
    quota_gb: float
    usage_ratio: float
    remaining_gb: float
    warning: bool
    exceeded: bool


# ============ Lifecycle Schemas ============

class TorrentScore(BaseModel):
    hash: str
    name: str
    score: float
    ratio: float
    seeding_time: int
    upload_speed: float
    download_speed: float
    status: str
    recommendation: str


class LifecycleActionRequest(BaseModel):
    downloader_id: int
    torrent_hashes: List[str]
    action: str
    archive_path: Optional[str] = None
