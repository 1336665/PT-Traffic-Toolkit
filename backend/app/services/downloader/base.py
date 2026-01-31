from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TorrentInfo:
    hash: str
    name: str
    size: int  # bytes
    progress: float  # 0-1
    status: str  # downloading, seeding, paused, etc.
    uploaded: int  # bytes
    downloaded: int  # bytes
    ratio: float
    upload_speed: int  # bytes/s
    download_speed: int  # bytes/s
    seeders: int
    leechers: int
    seeds_connected: int
    peers_connected: int
    tracker: str
    tags: List[str]
    category: str
    save_path: str
    added_time: Optional[datetime]
    seeding_time: int  # seconds
    next_announce_time: Optional[float] = None  # unix timestamp seconds
    announce_interval: Optional[int] = None  # seconds
    total_size: Optional[int] = None
    selected_size: Optional[int] = None
    completed: Optional[int] = None
    completed_time: Optional[datetime] = None
    state: Optional[str] = None
    tracker_status: str = ""


@dataclass
class DownloaderStats:
    upload_speed: int  # bytes/s
    download_speed: int  # bytes/s
    total_uploaded: int  # bytes
    total_downloaded: int  # bytes
    free_space: int  # bytes
    total_torrents: int
    active_torrents: int
    downloading_torrents: int
    seeding_torrents: int


class BaseDownloader(ABC):
    """Abstract base class for torrent client adapters"""

    def __init__(self, host: str, port: int, username: str = "", password: str = "", use_ssl: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self._client = None

    @property
    def base_url(self) -> str:
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the downloader and verify connection"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from the downloader"""
        pass

    @abstractmethod
    async def get_torrents(self) -> List[TorrentInfo]:
        """Get all torrents"""
        pass

    @abstractmethod
    async def get_torrent(self, torrent_hash: str) -> Optional[TorrentInfo]:
        """Get a specific torrent by hash"""
        pass

    @abstractmethod
    async def add_torrent(
        self,
        torrent: bytes | str,  # bytes for .torrent file, str for magnet link
        save_path: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paused: bool = False,
        upload_limit: int = 0,  # bytes/s, 0 = no limit
        download_limit: int = 0,
        sequential: bool = False,
        first_last_priority: bool = False,
    ) -> Optional[str]:
        """Add a torrent, return hash if successful"""
        pass

    @abstractmethod
    async def remove_torrent(self, torrent_hash: str, delete_files: bool = False) -> bool:
        """Remove a torrent"""
        pass

    @abstractmethod
    async def pause_torrent(self, torrent_hash: str) -> bool:
        """Pause a torrent"""
        pass

    @abstractmethod
    async def resume_torrent(self, torrent_hash: str) -> bool:
        """Resume a torrent"""
        pass

    @abstractmethod
    async def reannounce_torrent(self, torrent_hash: str) -> bool:
        """Force reannounce (report) a torrent"""
        pass

    @abstractmethod
    async def set_torrent_upload_limit(self, torrent_hash: str, limit: int) -> bool:
        """Set upload speed limit for a torrent (bytes/s)"""
        pass

    @abstractmethod
    async def set_torrent_download_limit(self, torrent_hash: str, limit: int) -> bool:
        """Set download speed limit for a torrent (bytes/s)"""
        pass

    @abstractmethod
    async def get_stats(self) -> DownloaderStats:
        """Get downloader statistics"""
        pass

    @abstractmethod
    async def get_free_space(self, path: Optional[str] = None) -> int:
        """Get free disk space in bytes"""
        pass

    @abstractmethod
    async def set_global_upload_limit(self, limit: int) -> bool:
        """Set global upload speed limit (bytes/s)"""
        pass

    @abstractmethod
    async def set_global_download_limit(self, limit: int) -> bool:
        """Set global download speed limit (bytes/s)"""
        pass

    @abstractmethod
    async def pause_all_torrents(self) -> bool:
        """Pause all torrents"""
        pass

    @abstractmethod
    async def resume_all_torrents(self) -> bool:
        """Resume all torrents"""
        pass

    async def add_torrent_file(
        self,
        file_content: bytes,
        **kwargs
    ) -> Optional[str]:
        """Convenience method to add a .torrent file"""
        return await self.add_torrent(file_content, **kwargs)

    async def add_magnet(
        self,
        magnet_link: str,
        **kwargs
    ) -> Optional[str]:
        """Convenience method to add a magnet link"""
        return await self.add_torrent(magnet_link, **kwargs)

    async def get_torrent_announce_info(self, torrent_hash: str) -> tuple[Optional[float], Optional[int]]:
        """Get next_announce time and interval from tracker info

        Returns:
            Tuple of (next_announce_time as unix timestamp, announce_interval in seconds)
            Default implementation returns (None, None)
        """
        return None, None

    def extract_tracker_domain(self, tracker_url: str) -> str:
        """Extract domain from tracker URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(tracker_url)
            return parsed.netloc
        except Exception:
            return ""
