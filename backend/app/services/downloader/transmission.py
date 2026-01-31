import asyncio
import base64
import random
from typing import List, Optional
from datetime import datetime
import httpx

from .base import BaseDownloader, TorrentInfo, DownloaderStats
from app.utils import get_logger

logger = get_logger('pt_manager.downloader.transmission')

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5
RETRY_MAX_DELAY = 10.0
RETRY_EXPONENTIAL_BASE = 2


class TransmissionClient(BaseDownloader):
    """Transmission RPC API client"""

    def __init__(self, host: str, port: int, username: str = "", password: str = "", use_ssl: bool = False):
        super().__init__(host, port, username, password, use_ssl)
        self._session: Optional[httpx.AsyncClient] = None
        self._session_id = ""
        self._rpc_path = "/transmission/rpc"

    async def connect(self) -> bool:
        try:
            auth = None
            if self.username:
                auth = (self.username, self.password)

            self._session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                verify=False,
                auth=auth,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )

            # Get session ID (Transmission requires X-Transmission-Session-Id header)
            response = await self._session.post(self._rpc_path, json={})

            if response.status_code == 409:
                # Get session ID from header
                self._session_id = response.headers.get("X-Transmission-Session-Id", "")
                if self._session_id:
                    # Verify connection
                    result = await self._rpc_call("session-get")
                    ok = result is not None
                    if not ok:
                        await self.disconnect()
                    return ok

            await self.disconnect()
            return False
        except Exception as e:
            logger.error(f"Transmission connection error: {e}")
            await self.disconnect()
            return False

    async def disconnect(self):
        if self._session:
            await self._session.aclose()
            self._session = None

    async def _rpc_call(self, method: str, arguments: dict = None, retries: int = MAX_RETRIES) -> Optional[dict]:
        if not self._session:
            return None

        last_error = None
        for attempt in range(retries):
            try:
                payload = {"method": method}
                if arguments:
                    payload["arguments"] = arguments

                response = await self._session.post(
                    self._rpc_path,
                    json=payload,
                    headers={"X-Transmission-Session-Id": self._session_id}
                )

                if response.status_code == 409:
                    # Session ID expired, get new one
                    self._session_id = response.headers.get("X-Transmission-Session-Id", "")
                    response = await self._session.post(
                        self._rpc_path,
                        json=payload,
                        headers={"X-Transmission-Session-Id": self._session_id}
                    )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("result") == "success":
                        return data.get("arguments", {})

                return None
            except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                logger.warning(f"Transmission RPC error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (RETRY_EXPONENTIAL_BASE ** attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Transmission RPC error: {e}")
                return None

        if last_error:
            logger.error(f"Transmission RPC failed after {retries} retries: {last_error}")
        return None

    def _parse_torrent(self, data: dict) -> TorrentInfo:
        """Parse Transmission torrent data to TorrentInfo"""
        status_map = {
            0: "paused",      # TR_STATUS_STOPPED
            1: "queued",      # TR_STATUS_CHECK_WAIT
            2: "checking",    # TR_STATUS_CHECK
            3: "queued",      # TR_STATUS_DOWNLOAD_WAIT
            4: "downloading", # TR_STATUS_DOWNLOAD
            5: "queued",      # TR_STATUS_SEED_WAIT
            6: "seeding",     # TR_STATUS_SEED
        }

        status_code = data.get("status", 0)
        status = status_map.get(status_code, "error")

        # Handle error states
        if data.get("error", 0) > 0:
            status = "error"

        added_date = data.get("addedDate", 0)
        added_time = datetime.fromtimestamp(added_date) if added_date else None

        # Calculate seeding time
        done_date = data.get("doneDate", 0)
        completed_time = datetime.fromtimestamp(done_date) if done_date else None
        if done_date > 0 and status == "seeding":
            seeding_time = int(datetime.now().timestamp() - done_date)
        else:
            seeding_time = data.get("secondsSeeding", 0)

        labels = data.get("labels", [])

        # Get tracker domain
        trackers = data.get("trackers", [])
        tracker = trackers[0].get("announce", "") if trackers else ""
        tracker_stats = data.get("trackerStats", [])
        next_announce_time = self._get_next_announce_time(tracker_stats)
        announce_interval = self._get_announce_interval(tracker_stats)
        tracker_status = ""

        # Extract seeders and leechers from trackerStats
        # Sum up from all trackers, taking the max values
        seeders = 0
        leechers = 0
        for stat in tracker_stats:
            # seederCount and leecherCount are the swarm totals from tracker
            seeder_count = stat.get("seederCount", 0)
            leecher_count = stat.get("leecherCount", 0)
            if seeder_count > seeders:
                seeders = seeder_count
            if leecher_count > leechers:
                leechers = leecher_count
            # Get tracker status from the first available
            if not tracker_status:
                tracker_status = stat.get("lastAnnounceResult", "") or str(stat.get("lastAnnouncePeerCount", ""))

        total_size = data.get("totalSize", 0)
        selected_size = data.get("sizeWhenDone", total_size)
        completed = data.get("haveValid", 0) + data.get("haveUnchecked", 0)
        return TorrentInfo(
            hash=data.get("hashString", ""),
            name=data.get("name", ""),
            size=data.get("totalSize", 0),
            progress=data.get("percentDone", 0),
            status=status,
            uploaded=data.get("uploadedEver", 0),
            downloaded=data.get("downloadedEver", 0),
            ratio=data.get("uploadRatio", 0),
            upload_speed=data.get("rateUpload", 0),
            download_speed=data.get("rateDownload", 0),
            seeders=seeders,
            leechers=leechers,
            seeds_connected=data.get("peersGettingFromUs", 0),
            peers_connected=data.get("peersSendingToUs", 0),
            tracker=tracker,
            tags=labels,
            category="",  # Transmission doesn't have categories
            save_path=data.get("downloadDir", ""),
            added_time=added_time,
            seeding_time=seeding_time,
            next_announce_time=next_announce_time,
            announce_interval=announce_interval,
            total_size=total_size,
            selected_size=selected_size,
            completed=completed,
            completed_time=completed_time,
            state=status,
            tracker_status=tracker_status,
        )

    def _get_next_announce_time(self, tracker_stats: list) -> Optional[float]:
        if not tracker_stats:
            return None
        next_times = []
        for stat in tracker_stats:
            value = stat.get("nextAnnounceTime")
            if value:
                try:
                    next_times.append(float(value))
                except (TypeError, ValueError):
                    continue
        if not next_times:
            return None
        return min(next_times)

    def _get_announce_interval(self, tracker_stats: list) -> Optional[int]:
        if not tracker_stats:
            return None
        intervals = []
        for stat in tracker_stats:
            value = stat.get("announceInterval")
            if value:
                try:
                    intervals.append(int(value))
                except (TypeError, ValueError):
                    continue
        if not intervals:
            return None
        return min(intervals)

    async def get_torrents(self) -> List[TorrentInfo]:
        fields = [
            "id", "hashString", "name", "totalSize", "percentDone", "status",
            "uploadedEver", "downloadedEver", "uploadRatio", "rateUpload",
            "rateDownload", "seeders", "leechers", "peersGettingFromUs",
            "peersSendingToUs", "trackers", "labels", "downloadDir",
            "addedDate", "doneDate", "secondsSeeding", "error", "trackerStats",
            "sizeWhenDone", "haveValid", "haveUnchecked"
        ]

        result = await self._rpc_call("torrent-get", {"fields": fields})
        if not result:
            return []

        torrents = result.get("torrents", [])
        return [self._parse_torrent(t) for t in torrents]

    async def get_torrent(self, torrent_hash: str) -> Optional[TorrentInfo]:
        fields = [
            "id", "hashString", "name", "totalSize", "percentDone", "status",
            "uploadedEver", "downloadedEver", "uploadRatio", "rateUpload",
            "rateDownload", "seeders", "leechers", "peersGettingFromUs",
            "peersSendingToUs", "trackers", "labels", "downloadDir",
            "addedDate", "doneDate", "secondsSeeding", "error", "trackerStats",
            "sizeWhenDone", "haveValid", "haveUnchecked"
        ]

        # Transmission uses ID or hash
        result = await self._rpc_call("torrent-get", {
            "ids": [torrent_hash],
            "fields": fields
        })

        if not result:
            return None

        torrents = result.get("torrents", [])
        if torrents:
            return self._parse_torrent(torrents[0])
        return None

    async def add_torrent(
        self,
        torrent: bytes | str,
        save_path: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        paused: bool = False,
        upload_limit: int = 0,
        download_limit: int = 0,
        sequential: bool = False,
        first_last_priority: bool = False,
    ) -> Optional[str]:
        arguments = {"paused": paused}

        if isinstance(torrent, bytes):
            arguments["metainfo"] = base64.b64encode(torrent).decode()
        else:
            arguments["filename"] = torrent

        if save_path:
            arguments["download-dir"] = save_path
        if tags:
            arguments["labels"] = tags

        result = await self._rpc_call("torrent-add", arguments)
        if not result:
            return None

        # Get hash from response
        torrent_added = result.get("torrent-added") or result.get("torrent-duplicate")
        if torrent_added:
            torrent_hash = torrent_added.get("hashString")

            # Set speed limits if specified
            if torrent_hash:
                if upload_limit > 0:
                    await self.set_torrent_upload_limit(torrent_hash, upload_limit)
                if download_limit > 0:
                    await self.set_torrent_download_limit(torrent_hash, download_limit)

            return torrent_hash

        return None

    async def remove_torrent(self, torrent_hash: str, delete_files: bool = False) -> bool:
        result = await self._rpc_call("torrent-remove", {
            "ids": [torrent_hash],
            "delete-local-data": delete_files
        })
        return result is not None

    async def pause_torrent(self, torrent_hash: str) -> bool:
        result = await self._rpc_call("torrent-stop", {"ids": [torrent_hash]})
        return result is not None

    async def resume_torrent(self, torrent_hash: str) -> bool:
        result = await self._rpc_call("torrent-start", {"ids": [torrent_hash]})
        return result is not None

    async def reannounce_torrent(self, torrent_hash: str) -> bool:
        result = await self._rpc_call("torrent-reannounce", {"ids": [torrent_hash]})
        return result is not None

    async def set_torrent_upload_limit(self, torrent_hash: str, limit: int) -> bool:
        # Transmission uses KB/s for limits
        limit_kbps = limit // 1024 if limit > 0 else 0
        result = await self._rpc_call("torrent-set", {
            "ids": [torrent_hash],
            "uploadLimited": limit > 0,
            "uploadLimit": limit_kbps
        })
        return result is not None

    async def set_torrent_download_limit(self, torrent_hash: str, limit: int) -> bool:
        limit_kbps = limit // 1024 if limit > 0 else 0
        result = await self._rpc_call("torrent-set", {
            "ids": [torrent_hash],
            "downloadLimited": limit > 0,
            "downloadLimit": limit_kbps
        })
        return result is not None

    async def get_stats(self) -> DownloaderStats:
        session = await self._rpc_call("session-stats")
        torrents = await self.get_torrents()

        if not session:
            return DownloaderStats(
                upload_speed=0,
                download_speed=0,
                total_uploaded=0,
                total_downloaded=0,
                free_space=0,
                total_torrents=len(torrents),
                active_torrents=0,
                downloading_torrents=0,
                seeding_torrents=0,
            )

        downloading = sum(1 for t in torrents if t.status == "downloading")
        seeding = sum(1 for t in torrents if t.status == "seeding")
        active = downloading + seeding

        cumulative = session.get("cumulative-stats", {})

        return DownloaderStats(
            upload_speed=session.get("uploadSpeed", 0),
            download_speed=session.get("downloadSpeed", 0),
            total_uploaded=cumulative.get("uploadedBytes", 0),
            total_downloaded=cumulative.get("downloadedBytes", 0),
            free_space=await self.get_free_space(),
            total_torrents=len(torrents),
            active_torrents=active,
            downloading_torrents=downloading,
            seeding_torrents=seeding,
        )

    async def get_free_space(self, path: Optional[str] = None) -> int:
        session = await self._rpc_call("session-get")
        if not session:
            return 0

        download_dir = path or session.get("download-dir", "")
        result = await self._rpc_call("free-space", {"path": download_dir})
        if result:
            return result.get("size-bytes", 0)
        return 0

    async def set_global_upload_limit(self, limit: int) -> bool:
        limit_kbps = limit // 1024 if limit > 0 else 0
        result = await self._rpc_call("session-set", {
            "speed-limit-up-enabled": limit > 0,
            "speed-limit-up": limit_kbps
        })
        return result is not None

    async def set_global_download_limit(self, limit: int) -> bool:
        limit_kbps = limit // 1024 if limit > 0 else 0
        result = await self._rpc_call("session-set", {
            "speed-limit-down-enabled": limit > 0,
            "speed-limit-down": limit_kbps
        })
        return result is not None

    async def pause_all_torrents(self) -> bool:
        """Pause all torrents using Transmission RPC"""
        result = await self._rpc_call("torrent-stop", {})
        return result is not None

    async def resume_all_torrents(self) -> bool:
        """Resume all torrents using Transmission RPC"""
        result = await self._rpc_call("torrent-start", {})
        return result is not None
