import json
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Downloader, SpeedLimitConfig, SpeedLimitRecord, SystemSettings
from app.services.downloader import TorrentInfo
from app.services.downloader.context import downloader_client
from app.utils import get_logger

logger = get_logger('pt_manager.speed_limit')


@dataclass
class ManagedTorrentState:
    hash: str
    name: str
    tags: List[str]
    category: str
    period_start_uploaded: int = 0
    period_start_time: float = 0.0
    current_uploaded: int = 0
    current_downloaded: int = 0
    progress: float = 0.0
    upload_speed: int = 0
    download_speed: int = 0
    brake_active: bool = False
    late_stage_limited: bool = False
    download_brake_active: bool = False
    upload_limit: int = 0
    download_limit: int = 0
    period_index: int = 0
    added_time: float = 0.0
    downloader_id: Optional[int] = None
    downloader_name: str = ""
    matched_by_tag: bool = False
    matched_by_category: bool = False

    @property
    def uploaded_this_period(self) -> int:
        return max(0, self.current_uploaded - self.period_start_uploaded)

    @property
    def elapsed_in_period(self) -> int:
        if self.period_start_time <= 0:
            return 0
        return max(0, int(time.time() - self.period_start_time))

    @property
    def current_period_avg_speed(self) -> int:
        elapsed = max(1, self.elapsed_in_period)
        return self.uploaded_this_period // elapsed


class SpeedLimiterService:
    STATE_KEY = "speed_limiter_v2_state"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.states: Dict[str, ManagedTorrentState] = {}

    async def get_config(self) -> Optional[SpeedLimitConfig]:
        result = await self.db.execute(select(SpeedLimitConfig).limit(1))
        return result.scalar_one_or_none()

    async def ensure_config(self) -> SpeedLimitConfig:
        config = await self.get_config()
        if config:
            return config
        config = SpeedLimitConfig()
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def save_state(self, commit: bool = True):
        payload = {torrent_hash: asdict(state) for torrent_hash, state in self.states.items()}
        result = await self.db.execute(select(SystemSettings).where(SystemSettings.key == self.STATE_KEY))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = json.dumps(payload)
        else:
            self.db.add(SystemSettings(key=self.STATE_KEY, value=json.dumps(payload)))
        if commit:
            await self.db.commit()

    async def load_state(self):
        result = await self.db.execute(select(SystemSettings).where(SystemSettings.key == self.STATE_KEY))
        setting = result.scalar_one_or_none()
        self.states = {}
        if not setting or not setting.value:
            return
        try:
            data = json.loads(setting.value)
            for torrent_hash, raw in data.items():
                self.states[torrent_hash] = ManagedTorrentState(**raw)
        except Exception as exc:
            logger.warning(f"Failed to load speed limiter state: {exc}")
            self.states = {}

    def _parse_csv_set(self, raw_value: str) -> Set[str]:
        return {item.strip() for item in (raw_value or '').split(',') if item.strip()}

    def _match_torrent(self, torrent: TorrentInfo, target_tags: Set[str], target_categories: Set[str]) -> tuple[bool, bool, bool]:
        torrent_tags = set(torrent.tags or [])
        matched_tag = bool(target_tags and torrent_tags.intersection(target_tags))
        matched_category = bool(target_categories and torrent.category and torrent.category in target_categories)
        return matched_tag or matched_category, matched_tag, matched_category

    def _initialize_state(self, torrent: TorrentInfo, downloader_id: int, downloader_name: str) -> ManagedTorrentState:
        now = time.time()
        added_time = torrent.added_time.timestamp() if torrent.added_time else now
        state = ManagedTorrentState(
            hash=torrent.hash,
            name=torrent.name,
            tags=list(torrent.tags or []),
            category=torrent.category or "",
            current_uploaded=torrent.uploaded,
            current_downloaded=torrent.downloaded,
            progress=torrent.progress or 0.0,
            upload_speed=torrent.upload_speed or 0,
            download_speed=torrent.download_speed or 0,
            added_time=added_time,
            downloader_id=downloader_id,
            downloader_name=downloader_name,
        )

        report_period = self._config.report_period_seconds
        state.period_index = max(0, int((now - added_time) // report_period))
        state.period_start_time = added_time + (state.period_index * report_period)
        state.period_start_uploaded = torrent.uploaded
        return state

    def _roll_period_if_needed(self, state: ManagedTorrentState):
        now = time.time()
        elapsed = now - state.period_start_time
        period_and_delay = self._config.report_period_seconds + self._config.recovery_delay_seconds
        if elapsed < period_and_delay:
            return
        periods_passed = max(1, int(elapsed // self._config.report_period_seconds))
        state.period_index += periods_passed
        state.period_start_time += periods_passed * self._config.report_period_seconds
        state.period_start_uploaded = state.current_uploaded
        state.brake_active = False
        state.late_stage_limited = False
        state.download_brake_active = False
        state.upload_limit = 0
        state.download_limit = 0

    def _update_logic(self, state: ManagedTorrentState):
        self._roll_period_if_needed(state)
        avg_speed = state.current_period_avg_speed
        uploaded_this_period = state.uploaded_this_period

        if uploaded_this_period >= self._config.brake_threshold_per_torrent:
            state.brake_active = True
            state.late_stage_limited = False
        elif state.progress >= self._config.progress_threshold:
            state.brake_active = False
            state.late_stage_limited = avg_speed > self._config.avg_speed_threshold_bps
        else:
            state.brake_active = False
            state.late_stage_limited = False

        if state.progress >= self._config.download_brake_progress_threshold and avg_speed > self._config.avg_speed_threshold_bps:
            state.download_brake_active = True

        if state.brake_active:
            state.upload_limit = self._config.brake_speed_bps
        elif state.late_stage_limited:
            state.upload_limit = self._config.late_stage_limit_bps
        else:
            state.upload_limit = 0

        if state.download_brake_active:
            state.download_limit = self._config.download_brake_speed_bps
        else:
            state.download_limit = 0

    async def apply_limits(self) -> Dict[str, Any]:
        self._config = await self.ensure_config()
        if not self._config.enabled:
            return {"enabled": False, "torrents": {}, "count": 0}

        target_tags = self._parse_csv_set(self._config.target_tags)
        target_categories = self._parse_csv_set(self._config.target_categories)

        result = await self.db.execute(select(Downloader).where(Downloader.enabled == True, Downloader.auto_speed_limit == True))
        downloaders = result.scalars().all()

        active_hashes: Set[str] = set()
        response: Dict[str, Any] = {}

        for downloader in downloaders:
            try:
                async with downloader_client(downloader) as client:
                    if not client:
                        continue
                    torrents = await client.get_torrents()
                    for torrent in torrents:
                        matched, matched_tag, matched_category = self._match_torrent(torrent, target_tags, target_categories)
                        if not matched:
                            continue

                        active_hashes.add(torrent.hash)
                        state = self.states.get(torrent.hash)
                        if state is None:
                            state = self._initialize_state(torrent, downloader.id, downloader.name)
                            self.states[torrent.hash] = state

                        state.name = torrent.name
                        state.tags = list(torrent.tags or [])
                        state.category = torrent.category or ""
                        state.current_uploaded = torrent.uploaded
                        state.current_downloaded = torrent.downloaded
                        state.progress = torrent.progress or 0.0
                        state.upload_speed = torrent.upload_speed or 0
                        state.download_speed = torrent.download_speed or 0
                        state.downloader_id = downloader.id
                        state.downloader_name = downloader.name
                        state.matched_by_tag = matched_tag
                        state.matched_by_category = matched_category

                        self._update_logic(state)

                        await client.set_torrent_upload_limit(torrent.hash, state.upload_limit)
                        await client.set_torrent_download_limit(torrent.hash, state.download_limit)

                        self.db.add(SpeedLimitRecord(
                            tracker_domain=torrent.tracker or '',
                            downloader_id=downloader.id,
                            current_speed=torrent.upload_speed or 0,
                            target_speed=self._config.upload_limit_bps,
                            limit_applied=state.upload_limit,
                            phase=self._status_code(state),
                            uploaded=0,
                            downloaded=0,
                            torrent_hash=torrent.hash,
                            torrent_name=torrent.name,
                            progress=state.progress,
                            upload_limit=state.upload_limit,
                            download_limit=state.download_limit,
                            period_uploaded=state.uploaded_this_period,
                            period_avg_speed=state.current_period_avg_speed,
                            period_index=state.period_index,
                            matched_by_tag=matched_tag,
                            matched_by_category=matched_category,
                            tags=','.join(state.tags),
                            category=state.category,
                        ))

                        response[torrent.hash] = self._serialize_state(state)
            except Exception as exc:
                logger.error(f"Failed processing downloader {downloader.name}: {exc}")

        removed_hashes = [torrent_hash for torrent_hash in self.states.keys() if torrent_hash not in active_hashes]
        for torrent_hash in removed_hashes:
            state = self.states[torrent_hash]
            try:
                if state.downloader_id:
                    downloader = next((d for d in downloaders if d.id == state.downloader_id), None)
                    if downloader:
                        async with downloader_client(downloader) as client:
                            if client:
                                await client.set_torrent_upload_limit(torrent_hash, 0)
                                await client.set_torrent_download_limit(torrent_hash, 0)
            except Exception:
                pass
            del self.states[torrent_hash]

        await self.save_state(commit=False)
        await self.db.commit()
        return {"enabled": True, "torrents": response, "count": len(response)}

    def _status_code(self, state: ManagedTorrentState) -> str:
        if state.brake_active:
            return 'period_brake'
        if state.download_brake_active and state.late_stage_limited:
            return 'dual_limit'
        if state.download_brake_active:
            return 'download_brake'
        if state.late_stage_limited:
            return 'upload_limit'
        return 'normal'

    def _serialize_state(self, state: ManagedTorrentState) -> Dict[str, Any]:
        now = time.time()
        elapsed = max(0, int(now - state.period_start_time))
        total = self._config.report_period_seconds
        remaining = max(0, total - elapsed)
        in_recovery = elapsed >= total and elapsed < total + self._config.recovery_delay_seconds
        recovery_remaining = max(0, total + self._config.recovery_delay_seconds - elapsed) if in_recovery else 0
        return {
            'name': state.name,
            'hash': state.hash,
            'tags': state.tags,
            'category': state.category,
            'progress': state.progress,
            'upload_speed': state.upload_speed,
            'download_speed': state.download_speed,
            'period_uploaded': state.uploaded_this_period,
            'period_avg_speed': state.current_period_avg_speed,
            'period_index': state.period_index,
            'period_elapsed': elapsed,
            'period_remaining': remaining,
            'recovery_remaining': recovery_remaining,
            'status': self._status_code(state),
            'upload_limit': state.upload_limit,
            'download_limit': state.download_limit,
            'brake_active': state.brake_active,
            'late_stage_limited': state.late_stage_limited,
            'download_brake_active': state.download_brake_active,
            'matched_by_tag': state.matched_by_tag,
            'matched_by_category': state.matched_by_category,
            'downloader_name': state.downloader_name,
        }

    async def clear_limits(self):
        result = await self.db.execute(select(Downloader).where(Downloader.enabled == True, Downloader.auto_speed_limit == True))
        downloaders = result.scalars().all()
        for downloader in downloaders:
            try:
                async with downloader_client(downloader) as client:
                    if not client:
                        continue
                    for torrent_hash in list(self.states.keys()):
                        await client.set_torrent_upload_limit(torrent_hash, 0)
                        await client.set_torrent_download_limit(torrent_hash, 0)
            except Exception as exc:
                logger.warning(f"Failed clearing limits on {downloader.name}: {exc}")
        self.states = {}
        await self.save_state()

    def get_status(self) -> Dict[str, Any]:
        return {torrent_hash: self._serialize_state(state) for torrent_hash, state in self.states.items()}

    async def get_cached_status(self) -> Dict[str, Any]:
        return self.get_status()

    def get_suggested_interval(self) -> float:
        return 5.0
