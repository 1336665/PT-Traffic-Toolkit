import base64
from typing import List, Optional
from datetime import datetime
import httpx
import json

from .base import BaseDownloader, TorrentInfo, DownloaderStats
from app.utils import get_logger

logger = get_logger('pt_manager.downloader.deluge')


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
                timeout=30.0,
                verify=False
            )

            # Login to Deluge WebUI
            result = await self._rpc_call("auth.login", [self.password])
            if not result:
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
            return False

    async def disconnect(self):
        if self._session:
            try:
                await self._rpc_call("auth.delete_session")
            except Exception:
                pass
            await self._session.aclose()
            self._session = None

    async def _rpc_call(self, method: str, params: list = None) -> Optional[any]:
        if not self._session:
            return None

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
        except Exception as e:
            logger.error(f"Deluge RPC error: {e}")
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
        )

    async def get_torrents(self) -> List[TorrentInfo]:
        fields = [
            "name", "state", "total_size", "progress", "total_uploaded",
            "total_done", "ratio", "upload_payload_rate", "download_payload_rate",
            "total_seeds", "total_peers", "num_seeds", "num_peers",
            "tracker_host", "tracker", "label", "save_path", "time_added",
            "seeding_time"
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
            "seeding_time"
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
