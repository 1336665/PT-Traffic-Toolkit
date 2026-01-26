"""
单元测试 - Downloader 客户端
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.downloader.base import TorrentInfo, DownloaderStats
from app.services.downloader.qbittorrent import QBittorrentClient
from app.services.downloader.transmission import TransmissionClient
from app.services.downloader.deluge import DelugeClient


class TestTorrentInfo:
    """测试 TorrentInfo 数据类"""

    def test_create_torrent_info(self):
        """测试创建 TorrentInfo"""
        info = TorrentInfo(
            hash="abc123",
            name="Test Torrent",
            size=1073741824,
            progress=0.5,
            status="downloading",
            uploaded=536870912,
            downloaded=268435456,
            ratio=2.0,
            upload_speed=1048576,
            download_speed=2097152,
            seeders=10,
            leechers=5,
            seeds_connected=3,
            peers_connected=2,
            tracker="https://tracker.example.com/announce",
            tags=["tag1", "tag2"],
            category="movies",
            save_path="/downloads/movies",
            added_time=datetime.now(),
            seeding_time=3600,
        )

        assert info.hash == "abc123"
        assert info.name == "Test Torrent"
        assert info.size == 1073741824
        assert info.progress == 0.5
        assert info.status == "downloading"
        assert info.ratio == 2.0


class TestDownloaderStats:
    """测试 DownloaderStats 数据类"""

    def test_create_downloader_stats(self):
        """测试创建 DownloaderStats"""
        stats = DownloaderStats(
            upload_speed=10485760,
            download_speed=20971520,
            total_uploaded=107374182400,
            total_downloaded=214748364800,
            free_space=536870912000,
            total_torrents=100,
            active_torrents=10,
            downloading_torrents=5,
            seeding_torrents=5,
        )

        assert stats.upload_speed == 10485760
        assert stats.download_speed == 20971520
        assert stats.total_torrents == 100


class TestQBittorrentClient:
    """测试 qBittorrent 客户端"""

    def test_init(self):
        """测试客户端初始化"""
        client = QBittorrentClient(
            host="localhost",
            port=8080,
            username="admin",
            password="adminadmin",
            use_ssl=False
        )

        assert client.host == "localhost"
        assert client.port == 8080
        assert client.username == "admin"
        assert client.base_url == "http://localhost:8080"

    def test_init_with_ssl(self):
        """测试 HTTPS 客户端初始化"""
        client = QBittorrentClient(
            host="localhost",
            port=8443,
            username="admin",
            password="adminadmin",
            use_ssl=True
        )

        assert client.base_url == "https://localhost:8443"

    def test_parse_torrent_downloading(self):
        """测试解析下载中的种子"""
        client = QBittorrentClient("localhost", 8080)

        data = {
            "hash": "abc123",
            "name": "Test.Torrent.2024.1080p",
            "size": 1073741824,
            "progress": 0.5,
            "state": "downloading",
            "uploaded": 536870912,
            "downloaded": 268435456,
            "ratio": 2.0,
            "upspeed": 1048576,
            "dlspeed": 2097152,
            "num_complete": 10,
            "num_incomplete": 5,
            "num_seeds": 3,
            "num_leechs": 2,
            "tracker": "https://tracker.example.com/announce",
            "tags": "tag1,tag2",
            "category": "movies",
            "save_path": "/downloads/movies",
            "added_on": int(datetime.now().timestamp()),
            "seeding_time": 0,
        }

        info = client._parse_torrent(data)

        assert info.hash == "abc123"
        assert info.name == "Test.Torrent.2024.1080p"
        assert info.status == "downloading"
        assert info.progress == 0.5

    def test_parse_torrent_seeding(self):
        """测试解析做种中的种子"""
        client = QBittorrentClient("localhost", 8080)

        data = {
            "hash": "def456",
            "name": "Test.Torrent.2024.1080p",
            "size": 1073741824,
            "progress": 1.0,
            "state": "uploading",
            "uploaded": 2147483648,
            "downloaded": 1073741824,
            "ratio": 2.0,
            "upspeed": 1048576,
            "dlspeed": 0,
            "num_complete": 10,
            "num_incomplete": 5,
            "num_seeds": 3,
            "num_leechs": 2,
            "tracker": "https://tracker.example.com/announce",
            "tags": "",
            "category": "",
            "save_path": "/downloads",
            "added_on": int(datetime.now().timestamp()),
            "seeding_time": 3600,
        }

        info = client._parse_torrent(data)

        assert info.status == "seeding"
        assert info.progress == 1.0
        assert info.seeding_time == 3600


class TestTransmissionClient:
    """测试 Transmission 客户端"""

    def test_init(self):
        """测试客户端初始化"""
        client = TransmissionClient(
            host="localhost",
            port=9091,
            username="admin",
            password="admin",
            use_ssl=False
        )

        assert client.host == "localhost"
        assert client.port == 9091
        assert client.base_url == "http://localhost:9091"

    def test_parse_torrent_seeding(self):
        """测试解析做种中的种子"""
        client = TransmissionClient("localhost", 9091)

        data = {
            "hashString": "abc123def456",
            "name": "Test.Torrent.2024",
            "totalSize": 1073741824,
            "percentDone": 1.0,
            "status": 6,  # TR_STATUS_SEED
            "uploadedEver": 2147483648,
            "downloadedEver": 1073741824,
            "uploadRatio": 2.0,
            "rateUpload": 1048576,
            "rateDownload": 0,
            "peersGettingFromUs": 3,
            "peersSendingToUs": 0,
            "trackers": [{"announce": "https://tracker.example.com/announce"}],
            "trackerStats": [
                {
                    "seederCount": 10,
                    "leecherCount": 5,
                    "lastAnnounceResult": "Success",
                }
            ],
            "labels": ["movies"],
            "downloadDir": "/downloads/movies",
            "addedDate": int(datetime.now().timestamp()),
            "doneDate": int(datetime.now().timestamp()) - 3600,
            "secondsSeeding": 3600,
            "sizeWhenDone": 1073741824,
            "haveValid": 1073741824,
            "haveUnchecked": 0,
        }

        info = client._parse_torrent(data)

        assert info.hash == "abc123def456"
        assert info.status == "seeding"
        assert info.seeders == 10
        assert info.leechers == 5


class TestDelugeClient:
    """测试 Deluge 客户端"""

    def test_init(self):
        """测试客户端初始化"""
        client = DelugeClient(
            host="localhost",
            port=8112,
            username="",
            password="deluge",
            use_ssl=False
        )

        assert client.host == "localhost"
        assert client.port == 8112
        assert client.base_url == "http://localhost:8112"

    def test_parse_torrent_downloading(self):
        """测试解析下载中的种子"""
        client = DelugeClient("localhost", 8112)

        data = {
            "name": "Test.Torrent.2024",
            "state": "Downloading",
            "total_size": 1073741824,
            "progress": 50.0,  # Deluge uses 0-100
            "total_uploaded": 536870912,
            "total_done": 536870912,
            "ratio": 1.0,
            "upload_payload_rate": 1048576,
            "download_payload_rate": 2097152,
            "total_seeds": 10,
            "total_peers": 5,
            "num_seeds": 3,
            "num_peers": 2,
            "tracker_host": "tracker.example.com",
            "label": "movies",
            "save_path": "/downloads/movies",
            "time_added": int(datetime.now().timestamp()),
            "seeding_time": 0,
            "trackers": [],
        }

        info = client._parse_torrent("abc123", data)

        assert info.hash == "abc123"
        assert info.status == "downloading"
        assert info.progress == 0.5  # Converted to 0-1 range
        assert info.category == "movies"


class TestRetryMechanism:
    """测试重试机制"""

    @pytest.mark.asyncio
    async def test_exponential_backoff_delay(self):
        """测试指数退避延迟计算"""
        import random
        from app.services.downloader.qbittorrent import (
            RETRY_BASE_DELAY,
            RETRY_EXPONENTIAL_BASE,
            RETRY_MAX_DELAY
        )

        # 模拟延迟计算
        delays = []
        for attempt in range(5):
            delay = min(
                RETRY_BASE_DELAY * (RETRY_EXPONENTIAL_BASE ** attempt),
                RETRY_MAX_DELAY
            )
            delays.append(delay)

        # 验证延迟递增
        assert delays[0] < delays[1] < delays[2]
        # 验证不超过最大延迟
        assert all(d <= RETRY_MAX_DELAY for d in delays)
