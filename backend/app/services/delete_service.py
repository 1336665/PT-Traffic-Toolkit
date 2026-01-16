from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeleteRule, DeleteRecord, Downloader, TorrentCache
from app.services.downloader import create_downloader, TorrentInfo
from app.utils import get_logger

logger = get_logger('pt_manager.delete')


class DeleteService:
    """Service for managing delete rules and executing torrent deletion"""

    # Field types for condition evaluation
    NUMERIC_FIELDS = {
        'progress', 'seeding_time', 'uploaded', 'downloaded', 'ratio',
        'upload_speed', 'download_speed', 'added_time', 'size', 'seeders',
        'leechers', 'seeds_connected', 'peers_connected'
    }

    STRING_FIELDS = {'tracker', 'tags', 'category', 'name', 'status'}

    # Unit conversions to base units
    UNIT_MULTIPLIERS = {
        # Time units to seconds
        'seconds': 1,
        'minutes': 60,
        'hours': 3600,
        'days': 86400,
        # Size units to bytes
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
        # Speed units to bytes/s
        'B/s': 1,
        'KB/s': 1024,
        'MB/s': 1024 ** 2,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._duration_cache: Dict[str, datetime] = {}  # torrent_hash -> condition_met_since

    def convert_value(self, value: float, unit: str) -> float:
        """Convert value to base unit"""
        multiplier = self.UNIT_MULTIPLIERS.get(unit, 1)
        return value * multiplier

    def get_torrent_field_value(self, torrent: TorrentInfo, field: str) -> Any:
        """Get field value from torrent info"""
        field_map = {
            'progress': lambda t: t.progress * 100,  # Return as percentage
            'seeding_time': lambda t: t.seeding_time,  # Already in seconds
            'uploaded': lambda t: t.uploaded,
            'downloaded': lambda t: t.downloaded,
            'ratio': lambda t: t.ratio,
            'upload_speed': lambda t: t.upload_speed,
            'download_speed': lambda t: t.download_speed,
            'size': lambda t: t.size,
            'seeders': lambda t: t.seeders,
            'leechers': lambda t: t.leechers,
            'seeds_connected': lambda t: t.seeds_connected,
            'peers_connected': lambda t: t.peers_connected,
            'tracker': lambda t: t.tracker,
            'tags': lambda t: ','.join(t.tags),
            'category': lambda t: t.category,
            'name': lambda t: t.name,
            'status': lambda t: t.status,
            # FIX: added_time now returns seconds (not days) for consistent unit conversion
            'added_time': lambda t: (datetime.utcnow() - t.added_time).total_seconds() if t.added_time else 0,
        }

        getter = field_map.get(field)
        if getter:
            return getter(torrent)
        return None

    def evaluate_condition(self, condition: dict, torrent: TorrentInfo) -> bool:
        """Evaluate a single condition against a torrent"""
        field = condition.get('field', '')
        operator = condition.get('operator', '')
        value = condition.get('value')
        unit = condition.get('unit', '')

        torrent_value = self.get_torrent_field_value(torrent, field)
        if torrent_value is None:
            return False

        # Convert value if needed
        if field in self.NUMERIC_FIELDS:
            compare_value = self.convert_value(float(value), unit)

            # Special handling for progress (already in percentage)
            if field == 'progress':
                compare_value = float(value)

            # Evaluate numeric comparison
            if operator == 'gt':
                return torrent_value > compare_value
            elif operator == 'lt':
                return torrent_value < compare_value
            elif operator == 'gte':
                return torrent_value >= compare_value
            elif operator == 'lte':
                return torrent_value <= compare_value
            elif operator == 'eq':
                return abs(torrent_value - compare_value) < 0.001

        elif field in self.STRING_FIELDS:
            torrent_str = str(torrent_value).lower()
            compare_str = str(value).lower()

            if operator == 'contains':
                return compare_str in torrent_str
            elif operator == 'not_contains':
                return compare_str not in torrent_str
            elif operator == 'eq':
                return torrent_str == compare_str
            elif operator == 'neq':
                return torrent_str != compare_str

        return False

    def evaluate_rule(self, rule: DeleteRule, torrent: TorrentInfo) -> bool:
        """Evaluate all conditions of a rule against a torrent"""
        if not rule.conditions:
            return False

        conditions = rule.conditions
        logic = rule.condition_logic.upper()

        results = [self.evaluate_condition(c, torrent) for c in conditions]

        if logic == 'AND':
            return all(results)
        elif logic == 'OR':
            return any(results)

        return False

    def check_tracker_filter(self, rule: DeleteRule, torrent: TorrentInfo) -> bool:
        """Check if torrent matches tracker filter"""
        if not rule.tracker_filter:
            return True

        tracker_domain = torrent.tracker.lower()
        filter_domain = rule.tracker_filter.lower()

        return filter_domain in tracker_domain

    def check_tag_filter(self, rule: DeleteRule, torrent: TorrentInfo) -> bool:
        """Check if torrent matches tag filter"""
        if not rule.tag_filter:
            return True

        torrent_tags = ','.join(torrent.tags).lower()
        filter_tag = rule.tag_filter.lower()

        return filter_tag in torrent_tags

    async def get_matching_torrents(
        self,
        rule: DeleteRule,
        downloader: Downloader
    ) -> List[Tuple[TorrentInfo, bool]]:
        """Get torrents matching a rule with duration check status"""
        matching = []

        try:
            client = create_downloader(downloader)
            if not await client.connect():
                return []

            torrents = await client.get_torrents()
            await client.disconnect()

            # Batch load duration cache for all torrents at once
            await self._load_duration_cache(downloader.id, [t.hash for t in torrents])

            torrents_to_update = []
            torrents_to_clear = []

            for torrent in torrents:
                # Check tracker and tag filters
                if not self.check_tracker_filter(rule, torrent):
                    continue
                if not self.check_tag_filter(rule, torrent):
                    continue

                # Evaluate rule conditions
                if self.evaluate_rule(rule, torrent):
                    # Check duration if configured
                    duration_met = True
                    if rule.duration_seconds > 0:
                        duration_met = self._check_duration_memory(
                            downloader.id, torrent.hash, rule.duration_seconds
                        )
                        torrents_to_update.append(torrent.hash)

                    matching.append((torrent, duration_met))
                else:
                    # Clear duration tracking if condition no longer matches
                    torrents_to_clear.append(torrent.hash)

            # Batch update database
            await self._batch_update_duration(downloader.id, torrents_to_update, torrents_to_clear)

            return matching
        except Exception as e:
            logger.error(f"Error getting matching torrents: {e}")
            return []

    async def _load_duration_cache(self, downloader_id: int, torrent_hashes: List[str]):
        """Load duration tracking data from database to memory cache"""
        if not torrent_hashes:
            return

        result = await self.db.execute(
            select(TorrentCache).where(
                TorrentCache.downloader_id == downloader_id,
                TorrentCache.torrent_hash.in_(torrent_hashes)
            )
        )
        caches = result.scalars().all()

        for cache in caches:
            if cache.condition_met_since:
                key = f"{downloader_id}:{cache.torrent_hash}"
                self._duration_cache[key] = cache.condition_met_since

    def _check_duration_memory(
        self,
        downloader_id: int,
        torrent_hash: str,
        required_seconds: int
    ) -> bool:
        """Check if torrent has matched conditions for required duration (memory-based)"""
        key = f"{downloader_id}:{torrent_hash}"
        now = datetime.utcnow()

        if key not in self._duration_cache:
            self._duration_cache[key] = now
            return False

        elapsed = (now - self._duration_cache[key]).total_seconds()
        return elapsed >= required_seconds

    async def _batch_update_duration(
        self,
        downloader_id: int,
        update_hashes: List[str],
        clear_hashes: List[str]
    ):
        """Batch update duration tracking in database"""
        now = datetime.utcnow()

        # Get existing cache entries
        all_hashes = list(set(update_hashes + clear_hashes))
        if not all_hashes:
            return

        result = await self.db.execute(
            select(TorrentCache).where(
                TorrentCache.downloader_id == downloader_id,
                TorrentCache.torrent_hash.in_(all_hashes)
            )
        )
        existing = {c.torrent_hash: c for c in result.scalars().all()}

        # Update or create entries for matched torrents
        for torrent_hash in update_hashes:
            key = f"{downloader_id}:{torrent_hash}"
            if torrent_hash in existing:
                cache = existing[torrent_hash]
                if cache.condition_met_since is None:
                    cache.condition_met_since = self._duration_cache.get(key, now)
            else:
                cache = TorrentCache(
                    downloader_id=downloader_id,
                    torrent_hash=torrent_hash,
                    name="",
                    condition_met_since=self._duration_cache.get(key, now)
                )
                self.db.add(cache)

        # Clear condition_met_since for non-matching torrents
        for torrent_hash in clear_hashes:
            key = f"{downloader_id}:{torrent_hash}"
            if key in self._duration_cache:
                del self._duration_cache[key]
            if torrent_hash in existing:
                existing[torrent_hash].condition_met_since = None

        # Single commit for all changes
        await self.db.commit()

    async def execute_rule(self, rule: DeleteRule) -> List[DeleteRecord]:
        """Execute a delete rule across all applicable downloaders"""
        deleted_records = []

        # Get applicable downloaders
        if rule.downloader_ids:
            result = await self.db.execute(
                select(Downloader).where(
                    Downloader.id.in_(rule.downloader_ids),
                    Downloader.enabled == True,
                    Downloader.auto_delete == True
                )
            )
        else:
            result = await self.db.execute(
                select(Downloader).where(
                    Downloader.enabled == True,
                    Downloader.auto_delete == True
                )
            )

        downloaders = result.scalars().all()
        delete_count = 0

        for downloader in downloaders:
            matching = await self.get_matching_torrents(rule, downloader)

            for torrent, duration_met in matching:
                # Check max delete count
                if rule.max_delete_count > 0 and delete_count >= rule.max_delete_count:
                    break

                # Skip if duration not met
                if not duration_met:
                    continue

                # Execute deletion
                success = await self._delete_torrent(
                    downloader, torrent, rule.delete_files, rule.force_report
                )

                if success:
                    record = DeleteRecord(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        downloader_id=downloader.id,
                        downloader_name=downloader.name,
                        torrent_hash=torrent.hash,
                        torrent_name=torrent.name,
                        size=torrent.size,
                        uploaded=torrent.uploaded,
                        downloaded=torrent.downloaded,
                        ratio=torrent.ratio,
                        seeding_time=torrent.seeding_time,
                        tracker=torrent.tracker,
                        files_deleted=rule.delete_files,
                        reported=rule.force_report,
                    )
                    self.db.add(record)
                    deleted_records.append(record)
                    delete_count += 1

                    # Clear from duration cache
                    key = f"{downloader.id}:{torrent.hash}"
                    if key in self._duration_cache:
                        del self._duration_cache[key]

        # Single commit for all records
        if deleted_records:
            await self.db.commit()

        return deleted_records

    async def _delete_torrent(
        self,
        downloader: Downloader,
        torrent: TorrentInfo,
        delete_files: bool,
        force_report: bool
    ) -> bool:
        """Delete a single torrent"""
        try:
            client = create_downloader(downloader)
            if not await client.connect():
                return False

            # Force report before deletion
            if force_report:
                await client.reannounce_torrent(torrent.hash)
                # Wait a bit for report
                import asyncio
                await asyncio.sleep(2)

            # Delete torrent
            success = await client.remove_torrent(torrent.hash, delete_files)
            await client.disconnect()

            if success:
                logger.info(f"Deleted torrent: {torrent.name[:50]} from {downloader.name}")

            return success
        except Exception as e:
            logger.error(f"Error deleting torrent: {e}")
            return False

    async def run_all_rules(self) -> List[DeleteRecord]:
        """Run all enabled delete rules"""
        result = await self.db.execute(
            select(DeleteRule)
            .where(DeleteRule.enabled == True)
            .order_by(DeleteRule.priority.desc())
        )
        rules = result.scalars().all()

        all_deleted = []
        for rule in rules:
            deleted = await self.execute_rule(rule)
            all_deleted.extend(deleted)

        return all_deleted
