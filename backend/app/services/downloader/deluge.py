import asyncio
import base64
import random
from typing import List, Optional
from datetime import datetime
import httpx
import json

from .base import BaseDownloader, TorrentInfo, DownloaderStats
from app.utils import get_logger

logger = get_logger('pt_manager.downloader.deluge')

# 重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5
RETRY_MAX_DELAY = 10.0
RETRY_EXPONENTIAL_BASE = 2


class DelugeClient(BaseDownloader):
    """Deluge WebUI JSON-RPC API client"""

    def __init__(self, host: str, port: int, username: str = "", password: str = "", use_ssl: bool = False):
        super().__init__(host, port, username, password, use_ssl)
        self._session: Optional[httpx.AsyncClient] = None
        self._request_id = 0

    async def connect(self) -> bool:
        try:
            self._session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                verify=False,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )

            # Login to Deluge WebUI
            result = await self._rpc_call("auth.login", [self.password])
            if not result:
                await self.disconnect()
                return False

            # Connect to daemon (if using web UI)
            # First check if already connected
            connected = await self._rpc_call("web.connected")
            if not connected:
                # Get available hosts
                hosts = await self._rpc_call("web.get_hosts")
                if hosts:
                    host_id = hosts[0][0]
                    await self._rpc_call("web.connect", [host_id])

            return True
        except Exception as e:
            logger.error(f"Deluge connection error: {e}")
            await self.disconnect()
            return False

    async def disconnect(self):
        if self._session:
            try:
                await self._rpc_call("auth.delete_session")
            except Exception:
                pass
            await self._session.aclose()
            self._session = None

    async def _rpc_call(self, method: str, params: list = None, retries: int = MAX_RETRIES) -> Optional[any]:
        if not self._session:
            return None

        last_error = None
        for attempt in range(retries):
            try:
                self._request_id += 1
                payload = {
                    "id": self._request_id,
                    "method": method,
                    "params": params or []
                }

                response = await self._session.post(
                    "/json",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("error") is None:
                        return data.get("result")

                return None
            except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                logger.warning(f"Deluge RPC error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    delay = min(
                        RETRY_BASE_DELAY * (RETRY_EXPONENTIAL_BASE ** attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Deluge RPC error: {e}")
                return None

        if last_error:
            logger.error(f"Deluge RPC failed after {retries} retries: {last_error}")
        return None

    def _parse_torrent(self, torrent_id: str, data: dict) -> TorrentInfo:
        """Parse Deluge torrent data to TorrentInfo"""
        state = data.get("state", "").lower()
        status_map = {
            "downloading": "downloading",
            "seeding": "seeding",
            "paused": "paused",
            "checking": "checking",
            "queued": "queued",
            "error": "error",
            "moving": "checking",
            "allocating": "checking",
        }
        status = status_map.get(state, "error")

        # Parse added time
        time_added = data.get("time_added", 0)
        added_time = datetime.fromtimestamp(time_added) if time_added else None

        # Get tracker from tracker_host
        tracker = data.get("tracker_host", "") or data.get("tracker", "")

        # Labels/tags
        label = data.get("label", "")
        tags = [label] if label else []
        trackers = data.get("trackers", [])
        next_announce_time = self._get_next_announce_time(trackers)
        announce_interval = self._get_announce_interval(trackers)
        tracker_status = ""
        for tracker_info in trackers:
            tracker_status = tracker_info.get("message", "") or tracker_info.get("status", "")
            if tracker_status:
                break

        total_size = data.get("total_size", 0)
        return TorrentInfo(
            hash=torrent_id,
            name=data.get("name", ""),
            size=data.get("total_size", 0),
            progress=data.get("progress", 0) / 100,  # Deluge uses 0-100
            status=status,
            uploaded=data.get("total_uploaded", 0),
            downloaded=data.get("total_done", 0),
            ratio=data.get("ratio", 0),
            upload_speed=data.get("upload_payload_rate", 0),
            download_speed=data.get("download_payload_rate", 0),
            seeders=data.get("total_seeds", 0),
            leechers=data.get("total_peers", 0),
            seeds_connected=data.get("num_seeds", 0),
            peers_connected=data.get("num_peers", 0),
            tracker=tracker,
            tags=tags,
            category=label,
            save_path=data.get("save_path", ""),
            added_time=added_time,
            seeding_time=data.get("seeding_time", 0),
            next_announce_time=next_announce_time,
            announce_interval=announce_interval,
            total_size=total_size,
            selected_size=total_size,
            completed=data.get("total_done", 0),
            completed_time=None,
            state=data.get("state", ""),
            tracker_status=tracker_status,
        )

    def _get_next_announce_time(self, trackers: list) -> Optional[float]:
        if not trackers:
            return None
        next_times = []
        for tracker in trackers:
            value = tracker.get("next_announce")
            if value:
                try:
                    next_times.append(float(value))
                except (TypeError, ValueError):
                    continue
        if not next_times:
            return None
        return min(next_times)

    def _get_announce_interval(self, trackers: list) -> Optional[int]:
        if not trackers:
            return None
        intervals = []
        for tracker in trackers:
            value = tracker.get("announce_interval")
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
            "name", "state", "total_size", "progress", "total_uploaded",
            "total_done", "ratio", "upload_payload_rate", "download_payload_rate",
            "total_seeds", "total_peers", "num_seeds", "num_peers",
            "tracker_host", "tracker", "label", "save_path", "time_added",
            "seeding_time", "trackers"
        ]

        result = await self._rpc_call("core.get_torrents_status", [{}, fields])
        if not result:
            return []

        return [self._parse_torrent(tid, tdata) for tid, tdata in result.items()]

    async def get_torrent(self, torrent_hash: str) -> Optional[TorrentInfo]:
        fields = [
            "name", "state", "total_size", "progress", "total_uploaded",
            "total_done", "ratio", "upload_payload_rate", "download_payload_rate",
            "total_seeds", "total_peers", "num_seeds", "num_peers",
            "tracker_host", "tracker", "label", "save_path", "time_added",
            "seeding_time", "trackers"
        ]

        result = await self._rpc_call("core.get_torrent_status", [torrent_hash, fields])
        if not result:
            return None

        return self._parse_torrent(torrent_hash, result)

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
        options = {"add_paused": paused}

        if save_path:
            options["download_location"] = save_path
        if upload_limit > 0:
            options["max_upload_speed"] = upload_limit / 1024  # KB/s
        if download_limit > 0:
            options["max_download_speed"] = download_limit / 1024

        if isinstance(torrent, bytes):
            # Add from file content
            torrent_b64 = base64.b64encode(torrent).decode()
            result = await self._rpc_call(
                "core.add_torrent_file",
                ["torrent.torrent", torrent_b64, options]
            )
        else:
            # Add from URL/magnet
            result = await self._rpc_call(
                "core.add_torrent_url",
                [torrent, options]
            )

        if result and category:
            # Set label if plugin is available
            await self._rpc_call("label.set_torrent", [result, category])

        return result

    async def remove_torrent(self, torrent_hash: str, delete_files: bool = False) -> bool:
        result = await self._rpc_call(
            "core.remove_torrent",
            [torrent_hash, delete_files]
        )
        return result is True

    async def pause_torrent(self, torrent_hash: str) -> bool:
        result = await self._rpc_call("core.pause_torrent", [[torrent_hash]])
        return result is not None

    async def resume_torrent(self, torrent_hash: str) -> bool:
        result = await self._rpc_call("core.resume_torrent", [[torrent_hash]])
        return result is not None

    async def reannounce_torrent(self, torrent_hash: str) -> bool:
        result = await self._rpc_call("core.force_reannounce", [[torrent_hash]])
        return result is not None

    async def set_torrent_upload_limit(self, torrent_hash: str, limit: int) -> bool:
        # Deluge uses KB/s, -1 for unlimited
        limit_kbps = limit / 1024 if limit > 0 else -1
        result = await self._rpc_call(
            "core.set_torrent_options",
            [[torrent_hash], {"max_upload_speed": limit_kbps}]
        )
        return result is not None

    async def set_torrent_download_limit(self, torrent_hash: str, limit: int) -> bool:
        limit_kbps = limit / 1024 if limit > 0 else -1
        result = await self._rpc_call(
            "core.set_torrent_options",
            [[torrent_hash], {"max_download_speed": limit_kbps}]
        )
        return result is not None

    async def get_stats(self) -> DownloaderStats:
        session = await self._rpc_call("core.get_session_status", [[
            "upload_rate", "download_rate", "total_upload", "total_download"
        ]])
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

        return DownloaderStats(
            upload_speed=session.get("upload_rate", 0),
            download_speed=session.get("download_rate", 0),
            total_uploaded=session.get("total_upload", 0),
            total_downloaded=session.get("total_download", 0),
            free_space=await self.get_free_space(),
            total_torrents=len(torrents),
            active_torrents=active,
            downloading_torrents=downloading,
            seeding_torrents=seeding,
        )

    async def get_free_space(self, path: Optional[str] = None) -> int:
        result = await self._rpc_call("core.get_free_space", [path] if path else [])
        return result or 0

    async def set_global_upload_limit(self, limit: int) -> bool:
        limit_kbps = limit / 1024 if limit > 0 else -1
        result = await self._rpc_call(
            "core.set_config",
            [{"max_upload_speed": limit_kbps}]
        )
        return result is not None

    async def set_global_download_limit(self, limit: int) -> bool:
        limit_kbps = limit / 1024 if limit > 0 else -1
        result = await self._rpc_call(
            "core.set_config",
            [{"max_download_speed": limit_kbps}]
        )
        return result is not None

    async def pause_all_torrents(self) -> bool:
        """Pause all torrents using Deluge RPC"""
        result = await self._rpc_call("core.pause_session")
        return result is not None

    async def resume_all_torrents(self) -> bool:
        """Resume all torrents using Deluge RPC"""
        result = await self._rpc_call("core.resume_session")
        return result is not None
