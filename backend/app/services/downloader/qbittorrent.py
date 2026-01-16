import asyncio
import hashlib
from typing import List, Optional
from datetime import datetime
import httpx

from .base import BaseDownloader, TorrentInfo, DownloaderStats
from app.utils import get_logger

logger = get_logger('pt_manager.downloader.qbittorrent')


class QBittorrentClient(BaseDownloader):
    """qBittorrent WebUI API client"""

    def __init__(self, host: str, port: int, username: str = "", password: str = "", use_ssl: bool = False):
        super().__init__(host, port, username, password, use_ssl)
        self._session: Optional[httpx.AsyncClient] = None
        self._cookies = {}

    async def connect(self) -> bool:
        try:
            self._session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                verify=False  # Allow self-signed certs
            )

            # Login
            response = await self._session.post(
                "/api/v2/auth/login",
                data={"username": self.username, "password": self.password}
            )

            if response.status_code == 200 and response.text == "Ok.":
                self._cookies = dict(response.cookies)
                return True

            # Try without auth (if qBittorrent has auth disabled)
            response = await self._session.get("/api/v2/app/version")
            if response.status_code == 200:
                return True

            return False
        except Exception as e:
            logger.error(f"qBittorrent connection error: {e}")
            return False

    async def disconnect(self):
        if self._session:
            try:
                await self._session.post("/api/v2/auth/logout", cookies=self._cookies)
            except Exception:
                pass
            await self._session.aclose()
            self._session = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Optional[httpx.Response]:
        if not self._session:
            return None
        try:
            kwargs.setdefault("cookies", self._cookies)
            response = await self._session.request(method, endpoint, **kwargs)
            return response if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"qBittorrent request error: {e}")
            return None

    def _parse_torrent(self, data: dict) -> TorrentInfo:
        """Parse qBittorrent torrent data to TorrentInfo"""
        status_map = {
            "downloading": "downloading",
            "stalledDL": "downloading",
            "metaDL": "downloading",
            "forcedDL": "downloading",
            "uploading": "seeding",
            "stalledUP": "seeding",
            "forcedUP": "seeding",
            "pausedDL": "paused",
            "pausedUP": "paused",
            "queuedDL": "queued",
            "queuedUP": "queued",
            "checkingDL": "checking",
            "checkingUP": "checking",
            "checkingResumeData": "checking",
            "error": "error",
            "missingFiles": "error",
            "moving": "checking",
            "unknown": "error",
        }

        state = data.get("state", "unknown")
        status = status_map.get(state, "error")

        added_on = data.get("added_on", 0)
        added_time = datetime.fromtimestamp(added_on) if added_on else None

        tags = data.get("tags", "")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        return TorrentInfo(
            hash=data.get("hash", ""),
            name=data.get("name", ""),
            size=data.get("total_size", 0),
            progress=data.get("progress", 0),
            status=status,
            uploaded=data.get("uploaded", 0),
            downloaded=data.get("downloaded", 0),
            ratio=data.get("ratio", 0),
            upload_speed=data.get("upspeed", 0),
            download_speed=data.get("dlspeed", 0),
            seeders=data.get("num_complete", 0),
            leechers=data.get("num_incomplete", 0),
            seeds_connected=data.get("num_seeds", 0),
            peers_connected=data.get("num_leechs", 0),
            tracker=data.get("tracker", ""),
            tags=tag_list,
            category=data.get("category", ""),
            save_path=data.get("save_path", ""),
            added_time=added_time,
            seeding_time=data.get("seeding_time", 0),
        )

    def _calculate_torrent_hash(self, torrent_data: bytes) -> Optional[str]:
        """Calculate info_hash from torrent file content"""
        try:
            # Simple bencode parser for info dict
            def decode_int(data: bytes, pos: int) -> tuple:
                end = data.index(b'e', pos)
                return int(data[pos+1:end]), end + 1

            def decode_string(data: bytes, pos: int) -> tuple:
                colon = data.index(b':', pos)
                length = int(data[pos:colon])
                start = colon + 1
                return data[start:start+length], start + length

            def decode(data: bytes, pos: int = 0) -> tuple:
                if data[pos:pos+1] == b'i':
                    return decode_int(data, pos)
                elif data[pos:pos+1] == b'l':
                    result = []
                    pos += 1
                    while data[pos:pos+1] != b'e':
                        item, pos = decode(data, pos)
                        result.append(item)
                    return result, pos + 1
                elif data[pos:pos+1] == b'd':
                    result = {}
                    pos += 1
                    while data[pos:pos+1] != b'e':
                        key, pos = decode_string(data, pos)
                        value, pos = decode(data, pos)
                        result[key] = value
                    return result, pos + 1
                else:
                    return decode_string(data, pos)

            # Find the info dict in the torrent data
            info_key = b'4:info'
            info_pos = torrent_data.find(info_key)
            if info_pos == -1:
                return None

            # Find the start and end of info dict
            info_start = info_pos + len(info_key)
            # We need to find where the dict ends
            depth = 0
            pos = info_start
            while pos < len(torrent_data):
                char = torrent_data[pos:pos+1]
                if char == b'd' or char == b'l':
                    depth += 1
                    pos += 1
                elif char == b'e':
                    if depth == 0:
                        break
                    depth -= 1
                    pos += 1
                elif char == b'i':
                    # Integer
                    end = torrent_data.index(b'e', pos)
                    pos = end + 1
                elif char.isdigit():
                    # String
                    colon = torrent_data.index(b':', pos)
                    length = int(torrent_data[pos:colon])
                    pos = colon + 1 + length
                else:
                    pos += 1

            info_data = torrent_data[info_start:pos+1]
            return hashlib.sha1(info_data).hexdigest().lower()
        except Exception as e:
            logger.debug(f"Failed to calculate torrent hash: {e}")
            return None

    async def get_torrents(self) -> List[TorrentInfo]:
        response = await self._request("GET", "/api/v2/torrents/info")
        if not response:
            return []

        try:
            data = response.json()
            return [self._parse_torrent(t) for t in data]
        except Exception as e:
            logger.error(f"Error parsing torrents: {e}")
            return []

    async def get_torrent(self, torrent_hash: str) -> Optional[TorrentInfo]:
        response = await self._request(
            "GET",
            "/api/v2/torrents/info",
            params={"hashes": torrent_hash}
        )
        if not response:
            return None

        try:
            data = response.json()
            if data:
                return self._parse_torrent(data[0])
            return None
        except Exception:
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
        data = {}
        files = {}
        expected_hash = None

        if isinstance(torrent, bytes):
            files["torrents"] = ("torrent.torrent", torrent, "application/x-bittorrent")
            # Calculate expected hash from torrent file
            expected_hash = self._calculate_torrent_hash(torrent)
        else:
            data["urls"] = torrent

        if save_path:
            data["savepath"] = save_path
        if category:
            data["category"] = category
        if tags:
            data["tags"] = ",".join(tags)
        if paused:
            data["paused"] = "true"
        if upload_limit > 0:
            data["upLimit"] = str(upload_limit)
        if download_limit > 0:
            data["dlLimit"] = str(download_limit)
        if sequential:
            data["sequentialDownload"] = "true"
        if first_last_priority:
            data["firstLastPiecePrio"] = "true"

        # Get current torrent hashes before adding
        existing_torrents = await self.get_torrents()
        existing_hashes = {t.hash for t in existing_torrents}

        response = await self._request(
            "POST",
            "/api/v2/torrents/add",
            data=data,
            files=files if files else None
        )

        if response and response.text == "Ok.":
            # If we calculated the hash, verify and return it
            if expected_hash:
                # Wait a bit for qBittorrent to process
                await asyncio.sleep(0.5)
                torrent_info = await self.get_torrent(expected_hash)
                if torrent_info:
                    return expected_hash

            # Fallback: find new torrents by comparing hashes
            max_retries = 5
            for _ in range(max_retries):
                await asyncio.sleep(0.5)
                current_torrents = await self.get_torrents()
                new_hashes = {t.hash for t in current_torrents} - existing_hashes
                if new_hashes:
                    # Return the first new hash found
                    return list(new_hashes)[0]

            logger.warning("Could not determine hash of added torrent")
            return None

        return None

    async def remove_torrent(self, torrent_hash: str, delete_files: bool = False) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/torrents/delete",
            data={
                "hashes": torrent_hash,
                "deleteFiles": "true" if delete_files else "false"
            }
        )
        return response is not None

    async def pause_torrent(self, torrent_hash: str) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/torrents/pause",
            data={"hashes": torrent_hash}
        )
        return response is not None

    async def resume_torrent(self, torrent_hash: str) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/torrents/resume",
            data={"hashes": torrent_hash}
        )
        return response is not None

    async def reannounce_torrent(self, torrent_hash: str) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/torrents/reannounce",
            data={"hashes": torrent_hash}
        )
        return response is not None

    async def set_torrent_upload_limit(self, torrent_hash: str, limit: int) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/torrents/setUploadLimit",
            data={"hashes": torrent_hash, "limit": str(limit)}
        )
        return response is not None

    async def set_torrent_download_limit(self, torrent_hash: str, limit: int) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/torrents/setDownloadLimit",
            data={"hashes": torrent_hash, "limit": str(limit)}
        )
        return response is not None

    async def get_stats(self) -> DownloaderStats:
        response = await self._request("GET", "/api/v2/transfer/info")
        torrents = await self.get_torrents()

        if not response:
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

        try:
            data = response.json()

            downloading = sum(1 for t in torrents if t.status == "downloading")
            seeding = sum(1 for t in torrents if t.status == "seeding")
            active = downloading + seeding

            return DownloaderStats(
                upload_speed=data.get("up_info_speed", 0),
                download_speed=data.get("dl_info_speed", 0),
                total_uploaded=data.get("up_info_data", 0),
                total_downloaded=data.get("dl_info_data", 0),
                free_space=await self.get_free_space(),
                total_torrents=len(torrents),
                active_torrents=active,
                downloading_torrents=downloading,
                seeding_torrents=seeding,
            )
        except Exception:
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

    async def get_free_space(self, path: Optional[str] = None) -> int:
        endpoint = "/api/v2/sync/maindata"
        response = await self._request("GET", endpoint)
        if not response:
            return 0

        try:
            data = response.json()
            return data.get("server_state", {}).get("free_space_on_disk", 0)
        except Exception:
            return 0

    async def set_global_upload_limit(self, limit: int) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/transfer/setUploadLimit",
            data={"limit": str(limit)}
        )
        return response is not None

    async def set_global_download_limit(self, limit: int) -> bool:
        response = await self._request(
            "POST",
            "/api/v2/transfer/setDownloadLimit",
            data={"limit": str(limit)}
        )
        return response is not None

    async def get_torrent_trackers(self, torrent_hash: str) -> List[dict]:
        """Get tracker info for a torrent"""
        response = await self._request(
            "GET",
            "/api/v2/torrents/trackers",
            params={"hash": torrent_hash}
        )
        if not response:
            return []

        try:
            return response.json()
        except Exception:
            return []
