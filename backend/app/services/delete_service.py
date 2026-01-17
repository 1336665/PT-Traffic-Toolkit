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
        'leechers', 'seeds_connected', 'peers_connected', 'total_size',
        'selected_size', 'completed', 'completed_time', 'true_ratio', 'ratio3',
        'free_space', 'leeching_count', 'seeding_count', 'global_upload_speed',
        'global_download_speed', 'second_from_zero'
    }

    STRING_FIELDS = {
        'tracker', 'tags', 'category', 'name', 'status', 'state', 'tracker_status',
        'save_path'
    }

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

    def _build_context(self, torrent: TorrentInfo, stats) -> Dict[str, Any]:
        now = datetime.utcnow()
        added_time_seconds = (now - torrent.added_time).total_seconds() if torrent.added_time else 0
        completed_time_seconds = (now - torrent.completed_time).total_seconds() if torrent.completed_time else 0
        size = torrent.selected_size or torrent.size
        total_size = torrent.total_size or torrent.size
        completed = torrent.completed if torrent.completed is not None else torrent.downloaded
        downloaded = torrent.downloaded
        uploaded = torrent.uploaded
        ratio = torrent.ratio
        true_ratio = uploaded / ((downloaded or size) if (downloaded or size) else 1)
        ratio3 = uploaded / (total_size or 1)
        return {
            # Numeric fields
            'progress': torrent.progress * 100,
            'seeding_time': torrent.seeding_time,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'ratio': ratio,
            'true_ratio': true_ratio,
            'ratio3': ratio3,
            'upload_speed': torrent.upload_speed,
            'download_speed': torrent.download_speed,
            'size': size,
            'total_size': total_size,
            'selected_size': size,
            'completed': completed,
            'added_time': added_time_seconds,
            'completed_time': completed_time_seconds,
            'seeders': torrent.seeders,
            'leechers': torrent.leechers,
            'seeds_connected': torrent.seeds_connected,
            'peers_connected': torrent.peers_connected,
            'free_space': stats.free_space if stats else 0,
            'leeching_count': stats.downloading_torrents if stats else 0,
            'seeding_count': stats.seeding_torrents if stats else 0,
            'global_upload_speed': stats.upload_speed if stats else 0,
            'global_download_speed': stats.download_speed if stats else 0,
            'second_from_zero': int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()),
            # String fields
            'tracker': torrent.tracker,
            'tracker_status': torrent.tracker_status or '',
            'tags': ','.join(torrent.tags),
            'category': torrent.category,
            'name': torrent.name,
            'status': torrent.status,
            'state': torrent.state or torrent.status,
            'save_path': torrent.save_path,
        }

    def _get_field_value(self, field: str, context: Dict[str, Any]) -> Any:
        field_map = {
            # Vertex-style keys
            'progress': 'progress',
            'seeding_time': 'seeding_time',
            'upload_speed': 'upload_speed',
            'download_speed': 'download_speed',
            'size': 'selected_size',
            'total_size': 'total_size',
            'seeders': 'seeders',
            'leechers': 'leechers',
            'added_time': 'added_time',
            'completed_time': 'completed_time',
            'uploaded': 'uploaded',
            'downloaded': 'downloaded',
            'ratio': 'ratio',
            'true_ratio': 'true_ratio',
            'ratio3': 'ratio3',
            'tracker': 'tracker',
            'tracker_status': 'tracker_status',
            'tags': 'tags',
            'category': 'category',
            'name': 'name',
            'status': 'status',
            'state': 'state',
            'save_path': 'save_path',
            'seeds_connected': 'seeds_connected',
            'peers_connected': 'peers_connected',
            'free_space': 'free_space',
            'leeching_count': 'leeching_count',
            'seeding_count': 'seeding_count',
            'global_upload_speed': 'global_upload_speed',
            'global_download_speed': 'global_download_speed',
            'second_from_zero': 'second_from_zero',
            # Vertex legacy camelCase
            'uploadSpeed': 'upload_speed',
            'downloadSpeed': 'download_speed',
            'totalSize': 'total_size',
            'trueRatio': 'true_ratio',
            'ratio3': 'ratio3',
            'addedTime': 'added_time',
            'completedTime': 'completed_time',
            'trackerStatus': 'tracker_status',
            'savePath': 'save_path',
            'seeder': 'seeders',
            'leecher': 'leechers',
            'freeSpace': 'free_space',
            'leechingCount': 'leeching_count',
            'seedingCount': 'seeding_count',
            'globalUploadSpeed': 'global_upload_speed',
            'globalDownloadSpeed': 'global_download_speed',
            'secondFromZero': 'second_from_zero',
        }
        mapped = field_map.get(field, field)
        return context.get(mapped)

    def _parse_numeric_value(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        try:
            parts = str(value).split('*')
            result = 1.0
            for part in parts:
                result *= float(part.strip())
            return result
        except (ValueError, TypeError):
            return 0.0

    def evaluate_condition(self, condition: dict, torrent: TorrentInfo, stats=None) -> bool:
        """Evaluate a single condition against a torrent"""
        field = condition.get('field') or condition.get('key', '')
        operator = condition.get('operator') or condition.get('compareType', '')
        value = condition.get('value')
        unit = condition.get('unit', '')

        context = self._build_context(torrent, stats)
        torrent_value = self._get_field_value(field, context)
        if torrent_value is None:
            return False

        # Convert value if needed
        if field in self.NUMERIC_FIELDS or isinstance(torrent_value, (int, float)):
            compare_value = self._parse_numeric_value(value)
            compare_value = self.convert_value(compare_value, unit)

            # Special handling for progress (already in percentage)
            if field in ['progress', 'progress_percent']:
                compare_value = float(value)

            if operator in ['gt', 'bigger']:
                return float(torrent_value) > compare_value
            if operator in ['lt', 'smaller']:
                return float(torrent_value) < compare_value
            if operator in ['gte']:
                return float(torrent_value) >= compare_value
            if operator in ['lte']:
                return float(torrent_value) <= compare_value
            if operator in ['eq', 'equals']:
                return abs(float(torrent_value) - compare_value) < 0.001

        elif field in self.STRING_FIELDS or isinstance(torrent_value, str):
            torrent_str = str(torrent_value).lower()
            compare_str = str(value).lower()
            compare_list = [item.strip().lower() for item in compare_str.split(',') if item.strip()]

            if operator in ['contains', 'contain']:
                return any(item in torrent_str for item in compare_list) if compare_list else compare_str in torrent_str
            if operator in ['not_contains', 'notContain']:
                return all(item not in torrent_str for item in compare_list) if compare_list else compare_str not in torrent_str
            if operator in ['includeIn']:
                return torrent_str in compare_list
            if operator in ['notIncludeIn']:
                return torrent_str not in compare_list
            if operator in ['eq', 'equals']:
                return torrent_str == compare_str
            if operator in ['neq']:
                return torrent_str != compare_str
            if operator in ['regExp']:
                try:
                    return re.search(compare_str, str(torrent_value)) is not None
                except re.error:
                    return False
            if operator in ['notRegExp']:
                try:
                    return re.search(compare_str, str(torrent_value)) is None
                except re.error:
                    return False

        return False

    def evaluate_rule(self, rule: DeleteRule, torrent: TorrentInfo, stats=None) -> bool:
        """Evaluate all conditions of a rule against a torrent"""
        if rule.rule_type == "javascript":
            return self._evaluate_js_rule(rule, torrent, stats)

        if not rule.conditions:
            return False

        conditions = rule.conditions
        logic = rule.condition_logic.upper()

        results = [self.evaluate_condition(c, torrent, stats) for c in conditions]

        if logic == 'AND':
            return all(results)
        if logic == 'OR':
            return any(results)

        return False

    def _evaluate_js_rule(self, rule: DeleteRule, torrent: TorrentInfo, stats=None) -> bool:
        try:
            import quickjs
        except Exception as e:
            logger.error(f"JavaScript rule requires quickjs: {e}")
            return False

        context = quickjs.Context()
        code = (rule.code or "").strip()
        if not code:
            return False

        if "=>" in code or code.startswith("function"):
            context.eval(f"var ruleFn = {code};")
        else:
            context.eval(f"var ruleFn = function(maindata, torrent) {{ {code} }};")

        maindata = {
            "freeSpace": stats.free_space if stats else 0,
            "leechingCount": stats.downloading_torrents if stats else 0,
            "seedingCount": stats.seeding_torrents if stats else 0,
            "globalUploadSpeed": stats.upload_speed if stats else 0,
            "globalDownloadSpeed": stats.download_speed if stats else 0,
        }
        context_values = self._build_context(torrent, stats)
        torrent_context = {
            "name": context_values["name"],
            "progress": context_values["progress"],
            "uploadSpeed": context_values["upload_speed"],
            "downloadSpeed": context_values["download_speed"],
            "category": context_values["category"],
            "tags": context_values["tags"],
            "size": context_values["selected_size"],
            "totalSize": context_values["total_size"],
            "state": context_values["state"],
            "tracker": context_values["tracker"],
            "trackerStatus": context_values["tracker_status"],
            "completed": context_values["completed"],
            "downloaded": context_values["downloaded"],
            "uploaded": context_values["uploaded"],
            "ratio": context_values["ratio"],
            "trueRatio": context_values["true_ratio"],
            "ratio3": context_values["ratio3"],
            "addedTime": context_values["added_time"],
            "completedTime": context_values["completed_time"],
            "savePath": context_values["save_path"],
            "seeder": context_values["seeders"],
            "leecher": context_values["leechers"],
            "freeSpace": context_values["free_space"],
            "leechingCount": context_values["leeching_count"],
            "seedingCount": context_values["seeding_count"],
            "globalUploadSpeed": context_values["global_upload_speed"],
            "globalDownloadSpeed": context_values["global_download_speed"],
            "secondFromZero": context_values["second_from_zero"],
        }
        return bool(context.call("ruleFn", maindata, torrent_context))

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
            try:
                stats = await client.get_stats()
            except Exception as e:
                logger.warning(f"Failed to get downloader stats: {e}")
                stats = None
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
                if self.evaluate_rule(rule, torrent, stats):
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

                action_taken = False
                if rule.limit_speed and rule.limit_speed > 0:
                    action_taken = await self._limit_torrent(
                        downloader, torrent, rule.limit_speed
                    )
                elif rule.pause:
                    action_taken = await self._pause_torrent(downloader, torrent)
                else:
                    delete_files = rule.delete_files and not rule.only_delete_torrent
                    action_taken = await self._delete_torrent(
                        downloader, torrent, delete_files, rule.force_report
                    )

                if action_taken:
                    delete_count += 1

                    if not rule.pause and not (rule.limit_speed and rule.limit_speed > 0):
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
                            files_deleted=delete_files,
                            reported=rule.force_report,
                        )
                        self.db.add(record)
                        deleted_records.append(record)

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

    async def _pause_torrent(self, downloader: Downloader, torrent: TorrentInfo) -> bool:
        try:
            client = create_downloader(downloader)
            if not await client.connect():
                return False
            success = await client.pause_torrent(torrent.hash)
            await client.disconnect()
            if success:
                logger.info(f"Paused torrent: {torrent.name[:50]} from {downloader.name}")
            return success
        except Exception as e:
            logger.error(f"Error pausing torrent: {e}")
            return False

    async def _limit_torrent(self, downloader: Downloader, torrent: TorrentInfo, limit_speed: int) -> bool:
        try:
            client = create_downloader(downloader)
            if not await client.connect():
                return False
            success = await client.set_torrent_download_limit(torrent.hash, limit_speed)
            await client.disconnect()
            if success:
                logger.info(
                    f"Limited torrent: {torrent.name[:50]} to {limit_speed} B/s on {downloader.name}"
                )
            return success
        except Exception as e:
            logger.error(f"Error limiting torrent: {e}")
            return False
