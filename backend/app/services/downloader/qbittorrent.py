import asyncio
import hashlib
import random
from typing import List, Optional
from datetime import datetime
import httpx

from .base import BaseDownloader, TorrentInfo, DownloaderStats
from app.utils import get_logger

logger = get_logger('pt_manager.downloader.qbittorrent')

# 连接重试配置
MAX_RETRIES = 3
RETRY_BASE_DELAY = 0.5  # 基础延迟（秒）
RETRY_MAX_DELAY = 10.0  # 最大延迟（秒）
RETRY_EXPONENTIAL_BASE = 2  # 指数退避基数


class QBittorrentClient(BaseDownloader):
    """qBittorrent WebUI API client"""

    def __init__(self, host: str, port: int, username: str = "", password: str = "", use_ssl: bool = False):
        super().__init__(host, port, username, password, use_ssl)
        self._session: Optional[httpx.AsyncClient] = None
        self._cookies = {}
        self._connected = False

    async def connect(self) -> bool:
        try:
            self._session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(30.0, connect=10.0),
                verify=False,  # Allow self-signed certs
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )

            # Login
            response = await self._session.post(
                "/api/v2/auth/login",
                data={"username": self.username, "password": self.password}
            )

            if response.status_code == 200 and response.text == "Ok.":
                self._cookies = dict(response.cookies)
                auth_check = await self._session.get(
                    "/api/v2/torrents/info",
                    params={"limit": 1},
                    cookies=self._cookies
                )
                ok = auth_check.status_code == 200
                if not ok:
                    await self.disconnect()
                else:
                    self._connected = True
                return ok

            if self.username or self.password:
                await self.disconnect()
                return False

            # Try without auth (if qBittorrent has auth disabled)
            response = await self._session.get("/api/v2/app/version")
            if response.status_code == 200:
                self._connected = True
                return True

            await self.disconnect()
            return False
        except Exception as e:
            logger.error(f"qBittorrent connection error: {e}")
            await self.disconnect()
            return False

    async def disconnect(self):
        self._connected = False
        if self._session:
            try:
                await self._session.post("/api/v2/auth/logout", cookies=self._cookies)
            except Exception:
                pass
            try:
                await self._session.aclose()
            except Exception:
                pass
            self._session = None

    async def _ensure_connected(self) -> bool:
        """确保连接有效，如果断开则尝试重连"""
        if self._session and self._connected:
            return True
        return await self.connect()

    async def _request(self, method: str, endpoint: str, retries: int = MAX_RETRIES, **kwargs) -> Optional[httpx.Response]:
        """发送请求，带指数退避重试机制"""
        if not self._session:
            if not await self._ensure_connected():
                return None

        last_error = None
        for attempt in range(retries):
            try:
                kwargs.setdefault("cookies", self._cookies)
                response = await self._session.request(method, endpoint, **kwargs)
                if 200 <= response.status_code < 300:
                    return response
                # 401 可能需要重新登录
                if response.status_code == 401:
                    logger.warning("qBittorrent session expired, reconnecting...")
                    self._connected = False
                    if await self._ensure_connected():
                        kwargs["cookies"] = self._cookies
                        continue
                return None
            except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                logger.warning(f"qBittorrent request error (attempt {attempt + 1}/{retries}): {e}")
                self._connected = False
                if attempt < retries - 1:
                    # 指数退避 + 随机抖动
                    delay = min(
                        RETRY_BASE_DELAY * (RETRY_EXPONENTIAL_BASE ** attempt) + random.uniform(0, 0.5),
                        RETRY_MAX_DELAY
                    )
                    await asyncio.sleep(delay)
                    if await self._ensure_connected():
                        kwargs["cookies"] = self._cookies
                        continue
            except Exception as e:
                logger.error(f"qBittorrent request error: {e}")
                return None

        if last_error:
            logger.error(f"qBittorrent request failed after {retries} retries: {last_error}")
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
        completion_on = data.get("completion_on", 0)
        completed_time = datetime.fromtimestamp(completion_on) if completion_on else None

        tags = data.get("tags", "")
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        next_announce_time = self._normalize_next_announce(data.get("next_announce"))

        total_size = data.get("total_size", 0) or data.get("size", 0)
        selected_size = data.get("size", total_size)
        completed = data.get("completed", data.get("downloaded", 0))
        return TorrentInfo(
            hash=data.get("hash", ""),
            name=data.get("name", ""),
            size=total_size,
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
            next_announce_time=next_announce_time,
            announce_interval=None,
            total_size=total_size,
            selected_size=selected_size,
            completed=completed,
            completed_time=completed_time,
            state=data.get("state"),
            tracker_status="",
        )

    def _normalize_next_announce(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        now = datetime.now().timestamp()
        # qBittorrent may return seconds-until or unix timestamp.
        if value > now + 60:
            return value
        return now + value

    async def get_torrent_trackers(self, torrent_hash: str) -> List[dict]:
        """Get tracker info for a torrent including next_announce time"""
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

    async def get_torrent_announce_info(self, torrent_hash: str) -> tuple[Optional[float], Optional[int]]:
        """Get next_announce time and interval from torrent properties

        按照 u2_magic.py 的方式，优先使用 torrents_properties 的 reannounce 字段

        Returns:
            Tuple of (next_announce_time as unix timestamp, announce_interval in seconds)
            next_announce_time: 下次汇报的 unix 时间戳，如果 reannounce=0 则返回 None
            announce_interval: 汇报间隔秒数
        """
        now = datetime.now().timestamp()
        best_next_announce = None
        best_interval = None
        reannounce_zero = False  # 标记是否遇到 reannounce=0

        # 方法1: 从 torrents_properties 获取 reannounce（u2_magic.py 的方式）
        try:
            response = await self._request(
                "GET",
                "/api/v2/torrents/properties",
                params={"hash": torrent_hash}
            )
            if response:
                props = response.json()
                reannounce = props.get("reannounce", -1)  # 使用 -1 区分"没有字段"和"字段值为0"
                if reannounce is not None:
                    if reannounce > 0:
                        best_next_announce = now + reannounce
                        logger.debug(f"从 properties 获取 reannounce: {reannounce}秒")
                    elif reannounce == 0:
                        # reannounce=0 通常表示刚刚汇报过，继续尝试从 trackers 获取
                        reannounce_zero = True
                        logger.debug(f"properties.reannounce=0, 可能刚汇报过")
        except Exception as e:
            logger.debug(f"获取 torrents_properties 失败: {e}")

        # 方法2: 从 trackers 获取（作为备份，或当 reannounce=0 时）
        trackers = await self.get_torrent_trackers(torrent_hash)

        for tracker in trackers:
            # Skip DHT, PeX, LSD (tier = -1 or url starts with ** )
            tier = tracker.get("tier", -1)
            url = tracker.get("url", "")
            if tier < 0 or url.startswith("**"):
                continue

            # Get next_announce (seconds until next announce)
            next_announce = tracker.get("next_announce", 0)
            if next_announce and next_announce > 0:
                announce_time = now + next_announce
                # 如果 properties 没获取到，或者 tracker 的值更近，使用 tracker 的值
                if best_next_announce is None or announce_time < best_next_announce:
                    best_next_announce = announce_time
                    logger.debug(f"从 trackers 获取 next_announce: {next_announce}秒")


            # Get announce interval if available.
            # qBittorrent trackers API may provide `interval` (regular announce interval)
            # and `min_announce` (forced announce minimum, usually 60s). We must avoid
            # using min_announce as the cycle interval. Prefer `interval` and filter
            # out obviously wrong small values (<300s).
            interval_value = tracker.get("interval") or tracker.get("announce_interval")
            try:
                if interval_value is not None:
                    interval_value = int(interval_value)
                    if interval_value >= 300:
                        if best_interval is None or interval_value > best_interval:
                            best_interval = interval_value
                            logger.debug(f"从 trackers 获取 interval: {interval_value}秒")
            except Exception:
                pass

            # 注意: min_announce 是强制汇报的最短间隔(通常60秒)，
            # 不是实际的汇报周期！不应该用作 announce_interval
            # 实际汇报周期应该通过种子年龄估算：7天内1800s，30天内2700s，30天外3600s

        # 如果 reannounce=0 且 trackers 也没有有效值，说明刚刚汇报过
        # 不在这里估算，让上层代码基于种子年龄估算

        return best_next_announce, best_interval

    def _calculate_torrent_hash(self, torrent_data: bytes) -> Optional[str]:
        """Calculate info_hash from torrent file content using proper bencode parsing"""
        try:
            def find_info_bounds(data: bytes, start: int) -> int:
                """Find the end position of a bencoded value starting at 'start'"""
                if start >= len(data):
                    return start
                char = data[start:start+1]
                if char == b'd':
                    # Dictionary: d<key><value>...e
                    pos = start + 1
                    while pos < len(data) and data[pos:pos+1] != b'e':
                        # Parse key (always a string)
                        pos = find_info_bounds(data, pos)
                        # Parse value
                        pos = find_info_bounds(data, pos)
                    return pos + 1  # Include the 'e'
                elif char == b'l':
                    # List: l<item>...e
                    pos = start + 1
                    while pos < len(data) and data[pos:pos+1] != b'e':
                        pos = find_info_bounds(data, pos)
                    return pos + 1  # Include the 'e'
                elif char == b'i':
                    # Integer: i<number>e
                    end = data.index(b'e', start)
                    return end + 1
                elif char.isdigit():
                    # String: <length>:<content>
                    colon = data.index(b':', start)
                    length = int(data[start:colon])
                    return colon + 1 + length
                else:
                    raise ValueError(f"Unknown bencode type at position {start}")

            # Find the info dict in the torrent data
            info_key = b'4:info'
            info_pos = torrent_data.find(info_key)
            if info_pos == -1:
                return None

            info_start = info_pos + len(info_key)
            info_end = find_info_bounds(torrent_data, info_start)

            info_data = torrent_data[info_start:info_end]
            return hashlib.sha1(info_data).hexdigest().lower()
        except Exception as e:
            logger.debug(f"Failed to calculate torrent hash: {e}")
            return None

    async def get_torrents(self, with_reannounce: bool = True) -> List[TorrentInfo]:
        """获取所有种子，可选批量获取 reannounce 信息"""
        response = await self._request("GET", "/api/v2/torrents/info")
        if not response:
            return []

        try:
            data = response.json()
            torrents = [self._parse_torrent(t) for t in data]

            # 批量获取活跃种子的 reannounce 信息
            if with_reannounce:
                active_torrents = [t for t in torrents if t.status in ['seeding', 'downloading']]
                # 并行获取所有活跃种子的 properties
                if active_torrents:
                    tasks = [self._get_torrent_reannounce(t.hash) for t in active_torrents]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # 更新种子的 next_announce_time
                    hash_to_reannounce = {}
                    for i, result in enumerate(results):
                        if isinstance(result, tuple) and result[0] is not None:
                            hash_to_reannounce[active_torrents[i].hash] = result

                    now = datetime.now().timestamp()
                    for torrent in torrents:
                        if torrent.hash in hash_to_reannounce:
                            next_ann, interval = hash_to_reannounce[torrent.hash]
                            if next_ann and next_ann > now:
                                torrent.next_announce_time = next_ann
                            if interval and interval > 0:
                                torrent.announce_interval = interval

            return torrents
        except Exception as e:
            logger.error(f"Error parsing torrents: {e}")
            return []

    async def _get_torrent_reannounce(self, torrent_hash: str) -> tuple[Optional[float], Optional[int]]:
        """快速获取单个种子的 reannounce 时间和汇报间隔

        优先使用 properties.reannounce，同时从 trackers 获取 interval
        确保返回尽可能完整的信息用于精确限速计算
        """
        now = datetime.now().timestamp()
        best_next_announce = None
        best_interval = None
        reannounce_zero = False

        # 1. 从 properties 获取 reannounce
        try:
            response = await self._request(
                "GET",
                "/api/v2/torrents/properties",
                params={"hash": torrent_hash},
                retries=1
            )
            if response:
                props = response.json()
                reannounce = props.get("reannounce", -1)
                if reannounce is not None:
                    if reannounce > 0:
                        best_next_announce = now + reannounce
                    elif reannounce == 0:
                        reannounce_zero = True
        except Exception:
            pass

        # 2. 从 trackers 获取 interval（即使有 reannounce 也获取，因为 interval 对计算很重要）
        try:
            response = await self._request(
                "GET",
                "/api/v2/torrents/trackers",
                params={"hash": torrent_hash},
                retries=1
            )
            if response:
                trackers = response.json()
                for tracker in trackers:
                    tier = tracker.get("tier", -1)
                    url = tracker.get("url", "")
                    if tier < 0 or url.startswith("**"):
                        continue

                    # 注意: min_announce 是强制汇报的最短间隔，不是实际汇报周期
                    # 不使用 min_announce 作为 interval

                    # interval 是 tracker 下发的实际汇报周期（秒），用于更精确的限速计算
                    interval_value = tracker.get("interval")
                    if isinstance(interval_value, (int, float)) and interval_value >= 300:
                        iv = int(interval_value)
                        if best_interval is None:
                            best_interval = iv
                        else:
                            # 多 tracker 时取更小的 interval（更保守）
                            best_interval = min(best_interval, iv)

                    # 如果 properties 没有获取到，尝试从 trackers 获取 next_announce
                    if best_next_announce is None:
                        next_announce = tracker.get("next_announce", 0)
                        if next_announce and next_announce > 0:
                            announce_time = now + next_announce
                            if best_next_announce is None or announce_time < best_next_announce:
                                best_next_announce = announce_time
        except Exception:
            pass

        # 3. 如果 reannounce=0，说明刚刚汇报过
        # 不在这里设置默认值，让 speed_limiter.py 根据种子年龄计算正确的 cycle_interval
        # 这样可以保证老种子使用正确的汇报间隔（30分/45分/60分）
        # reannounce_zero 标记已记录，返回 None 让上层处理

        return (best_next_announce, best_interval)

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

    async def pause_all_torrents(self) -> bool:
        """Pause all torrents using qBittorrent API"""
        response = await self._request(
            "POST",
            "/api/v2/torrents/pause",
            data={"hashes": "all"}
        )
        return response is not None

    async def resume_all_torrents(self) -> bool:
        """Resume all torrents using qBittorrent API"""
        response = await self._request(
            "POST",
            "/api/v2/torrents/resume",
            data={"hashes": "all"}
        )
        return response is not None
