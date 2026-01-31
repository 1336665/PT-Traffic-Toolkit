from typing import Optional
from app.models import DownloaderType, Downloader
from .base import BaseDownloader, TorrentInfo, DownloaderStats
from .qbittorrent import QBittorrentClient
from .transmission import TransmissionClient
from .deluge import DelugeClient


def create_downloader(downloader: Downloader) -> BaseDownloader:
    """Factory function to create appropriate downloader client"""
    if downloader.type == DownloaderType.QBITTORRENT:
        return QBittorrentClient(
            host=downloader.host,
            port=downloader.port,
            username=downloader.username,
            password=downloader.password,
            use_ssl=downloader.use_ssl,
        )
    elif downloader.type == DownloaderType.TRANSMISSION:
        return TransmissionClient(
            host=downloader.host,
            port=downloader.port,
            username=downloader.username,
            password=downloader.password,
            use_ssl=downloader.use_ssl,
        )
    elif downloader.type == DownloaderType.DELUGE:
        return DelugeClient(
            host=downloader.host,
            port=downloader.port,
            username=downloader.username,
            password=downloader.password,
            use_ssl=downloader.use_ssl,
        )
    else:
        raise ValueError(f"Unknown downloader type: {downloader.type}")


__all__ = [
    "BaseDownloader",
    "TorrentInfo",
    "DownloaderStats",
    "QBittorrentClient",
    "TransmissionClient",
    "DelugeClient",
    "create_downloader",
]
