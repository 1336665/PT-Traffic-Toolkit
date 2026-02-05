from datetime import datetime, timedelta
import importlib
import importlib.util
import re
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeleteRule, DeleteRecord, Downloader, TorrentCache
from app.services.downloader import TorrentInfo
from app.services.downloader.context import downloader_client
from app.services.notification import notify_delete, notify_delete_batch
from app.utils import get_logger

logger = get_logger('pt_manager.delete')


class DeleteService:
    """Service for managing delete rules and executing torrent deletion"""

    # Field types for condition evaluation (includes both snake_case and camelCase)
    NUMERIC_FIELDS = {
        # snake_case
        'progress', 'seeding_time', 'uploaded', 'downloaded', 'ratio',
        'upload_speed', 'download_speed', 'added_time', 'size', 'seeders',
        'leechers', 'seeds_connected', 'peers_connected', 'total_size',
        'selected_size', 'completed', 'completed_time', 'true_ratio', 'ratio3',
        'free_space', 'leeching_count', 'seeding_count', 'global_upload_speed',
        'global_download_speed', 'second_from_zero',
        # camelCase (frontend uses these)
        'uploadSpeed', 'downloadSpeed', 'addedTime', 'completedTime',
        'totalSize', 'selectedSize', 'trueRatio', 'freeSpace',
        'leechingCount', 'seedingCount', 'globalUploadSpeed', 'globalDownloadSpeed',
        'secondFromZero', 'seeder', 'leecher'
    }

    STRING_FIELDS = {
        'tracker', 'tags', 'category', 'name', 'status', 'state', 'tracker_status',
        'save_path', 'trackerStatus', 'savePath'
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

    # Fields that use GB as frontend display unit (backend stores bytes)
    SIZE_FIELDS_GB = {
        'size', 'totalSize', 'total_size', 'completed', 'downloaded',
        'uploaded', 'freeSpace', 'free_space', 'selected_size'
    }

    # Fields that use KB/s as frontend display unit (backend stores bytes/s)
    SPEED_FIELDS_KBS = {
        'uploadSpeed', 'upload_speed', 'downloadSpeed', 'download_speed',
        'globalUploadSpeed', 'global_upload_speed',
        'globalDownloadSpeed', 'global_download_speed'
    }

    # Fields that use seconds as display unit (no conversion needed)
    TIME_FIELDS_SECONDS = {
        'seeding_time', 'addedTime', 'added_time', 'completedTime',
        'completed_time', 'secondFromZero', 'second_from_zero'
    }

    # Fields with no unit (ratio, percentage, count)
    NO_UNIT_FIELDS = {
        'ratio', 'trueRatio', 'true_ratio', 'ratio3', 'progress',
        'seeders', 'leechers', 'seeder', 'leecher',
        'seeds_connected', 'peers_connected',
        'leechingCount', 'leeching_count', 'seedingCount', 'seeding_count'
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        # Duration tracking cache.
        # IMPORTANT: Must be per-rule to avoid different rules clearing/resetting each other's timers.
        # key format: "{downloader_id}:{rule_id}:{torrent_hash}" -> condition_met_since (UTC naive)
        self._duration_cache: Dict[str, datetime] = {}

    @staticmethod
    def _duration_cache_key(downloader_id: int, rule_id: int, torrent_hash: str) -> str:
        return f"{downloader_id}:{rule_id}:{torrent_hash}"

    @staticmethod
    def _duration_db_key(rule_id: int, torrent_hash: str) -> str:
        # Store rule id in the DB key so each rule has its own timer per torrent.
        # This avoids schema migrations while fixing multi-rule interference.
        return f"r{rule_id}:{torrent_hash}"

    def convert_value(self, value: float, unit: str) -> float:
        """Convert value to base unit"""
        multiplier = self.UNIT_MULTIPLIERS.get(unit, 1)
        return value * multiplier

    def _build_context(self, torrent: TorrentInfo, stats) -> Dict[str, Any]:
        now = datetime.now()
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

    def _get_field_unit_multiplier(self, field: str) -> float:
        """Get the unit multiplier for a field based on frontend display unit.

        Frontend displays:
        - Size fields: GB (user inputs GB, backend stores bytes)
        - Speed fields: KB/s (user inputs KB/s, backend stores bytes/s)
        - Time fields: seconds (no conversion needed)
        - Other numeric fields: no unit conversion
        """
        if field in self.SIZE_FIELDS_GB:
            # Frontend shows GB, convert user input (GB) to bytes
            return 1024 ** 3  # 1 GB = 1024^3 bytes
        elif field in self.SPEED_FIELDS_KBS:
            # Frontend shows KB/s, convert user input (KB/s) to bytes/s
            return 1024  # 1 KB/s = 1024 bytes/s
        elif field in self.TIME_FIELDS_SECONDS:
            # Frontend shows seconds, no conversion needed
            return 1
        elif field in self.NO_UNIT_FIELDS:
            # No unit conversion for ratio, percentage, count fields
            return 1
        else:
            # Default: no conversion
            return 1

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

            # If explicit unit is provided, use it
            if unit:
                compare_value = self.convert_value(compare_value, unit)
            else:
                # Auto-convert based on field type (frontend display unit -> backend unit)
                multiplier = self._get_field_unit_multiplier(field)
                compare_value = compare_value * multiplier

            # Special handling for progress (already in percentage, no conversion)
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
        """Evaluate JavaScript-based delete rule.

        SECURITY NOTE: JavaScript rules execute user-provided code.
        - quickjs is preferred as it provides better sandboxing
        - js2py is less secure and should be avoided in production
        - Code length and complexity are limited for safety
        """
        # Security: Limit code length to prevent DoS
        MAX_CODE_LENGTH = 10000

        engine = None
        quickjs = None
        js2py = None
        if importlib.util.find_spec("quickjs"):
            quickjs = importlib.import_module("quickjs")
            engine = "quickjs"
        elif importlib.util.find_spec("js2py"):
            js2py = importlib.import_module("js2py")
            engine = "js2py"
            logger.warning(
                "Using js2py for JavaScript rule evaluation. "
                "Consider installing quickjs for better security sandboxing."
            )
        else:
            logger.error("JavaScript rule engine missing: quickjs or js2py required")
            return False

        code = (rule.code or "").strip()
        if not code:
            return False

        # Security: Check code length
        if len(code) > MAX_CODE_LENGTH:
            logger.error(f"JavaScript rule code exceeds maximum length ({MAX_CODE_LENGTH} chars)")
            return False

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

        def normalize_js_function(raw_code: str, target_engine: str) -> str:
            if "=>" in raw_code and target_engine == "js2py":
                match = re.match(r"^\s*\((.*?)\)\s*=>\s*{(.*)}\s*$", raw_code, re.S)
                if match:
                    args, body = match.groups()
                    return f"function({args}) {{{body}}}"
            return raw_code

        if "=>" in code or code.startswith("function"):
            function_code = normalize_js_function(code, engine)
        else:
            function_code = f"function(maindata, torrent) {{ {code} }}"

        if engine == "quickjs":
            context = quickjs.Context()
            context.eval(f"var ruleFn = {function_code};")
            return bool(context.call("ruleFn", maindata, torrent_context))

        context = js2py.EvalJs({})
        context.execute(f"var ruleFn = {function_code};")
        return bool(context.ruleFn(maindata, torrent_context))

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

    def _get_rule_duration_seconds(self, rule: DeleteRule) -> int:
        """Get the maximum duration in seconds from rule conditions or rule-level duration.

        Checks both:
        1. Rule-level duration_seconds (legacy)
        2. Per-condition duration with duration_unit (new format from frontend)

        Returns the maximum duration found.
        """
        max_duration = rule.duration_seconds or 0

        # Check per-condition durations
        if rule.conditions:
            for condition in rule.conditions:
                cond_duration = condition.get('duration', 0)
                cond_unit = condition.get('duration_unit', 'seconds')

                if cond_duration and cond_duration > 0:
                    # Convert to seconds based on unit
                    multiplier = self.UNIT_MULTIPLIERS.get(cond_unit, 1)
                    duration_seconds = int(cond_duration * multiplier)
                    max_duration = max(max_duration, duration_seconds)

        return max_duration

    async def get_matching_torrents(
        self,
        rule: DeleteRule,
        downloader: Downloader
    ) -> List[Tuple[TorrentInfo, bool]]:
        """Get torrents matching a rule with duration check status"""
        matching: List[Tuple[TorrentInfo, bool]] = []

        try:
            async with downloader_client(downloader) as client:
                if not client:
                    return []

                torrents = await client.get_torrents()
                try:
                    stats = await client.get_stats()
                except Exception as e:
                    logger.warning(f"Failed to get downloader stats: {e}")
                    stats = None

            # Batch load duration cache for all torrents at once
            await self._load_duration_cache(rule.id, downloader.id, [t.hash for t in torrents])

            torrents_to_update: List[str] = []
            torrents_to_clear: List[str] = []

            # Get the effective duration for this rule (from conditions or rule-level)
            rule_duration_seconds = self._get_rule_duration_seconds(rule)

            for torrent in torrents:
                # Check tracker and tag filters
                if not self.check_tracker_filter(rule, torrent):
                    continue
                if not self.check_tag_filter(rule, torrent):
                    continue

                # Evaluate rule conditions
                if self.evaluate_rule(rule, torrent, stats):
                    # Check duration if configured (either rule-level or condition-level)
                    duration_met = True
                    if rule_duration_seconds > 0:
                        duration_met = self._check_duration_memory(
                            downloader.id, rule.id, torrent.hash, rule_duration_seconds
                        )
                        torrents_to_update.append(torrent.hash)

                    matching.append((torrent, duration_met))
                else:
                    # Clear duration tracking if condition no longer matches
                    torrents_to_clear.append(torrent.hash)

            # Batch update database
            await self._batch_update_duration(rule.id, downloader.id, torrents_to_update, torrents_to_clear)

            return matching
        except Exception as e:
            logger.error(f"Error getting matching torrents: {e}")
            return []
    async def _load_duration_cache(self, rule_id: int, downloader_id: int, torrent_hashes: List[str]):
        """Load duration tracking data from database to memory cache"""
        if not torrent_hashes:
            return

        # DB stores duration tracking entries keyed by rule to avoid cross-rule interference.
        db_hashes = [self._duration_db_key(rule_id, h) for h in torrent_hashes]
        db_to_raw = {self._duration_db_key(rule_id, h): h for h in torrent_hashes}

        result = await self.db.execute(
            select(TorrentCache).where(
                TorrentCache.downloader_id == downloader_id,
                TorrentCache.torrent_hash.in_(db_hashes)
            )
        )
        caches = result.scalars().all()

        for cache in caches:
            if cache.condition_met_since:
                raw_hash = db_to_raw.get(cache.torrent_hash)
                if not raw_hash:
                    continue
                key = self._duration_cache_key(downloader_id, rule_id, raw_hash)
                self._duration_cache[key] = cache.condition_met_since

    def _check_duration_memory(
        self,
        downloader_id: int,
        rule_id: int,
        torrent_hash: str,
        required_seconds: int
    ) -> bool:
        """Check if torrent has matched conditions for required duration (memory-based)"""
        key = self._duration_cache_key(downloader_id, rule_id, torrent_hash)
        now = datetime.utcnow()

        if key not in self._duration_cache:
            self._duration_cache[key] = now
            return False

        elapsed = (now - self._duration_cache[key]).total_seconds()
        return elapsed >= required_seconds

    async def _batch_update_duration(
        self,
        rule_id: int,
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

        all_db_hashes = [self._duration_db_key(rule_id, h) for h in all_hashes]

        result = await self.db.execute(
            select(TorrentCache).where(
                TorrentCache.downloader_id == downloader_id,
                TorrentCache.torrent_hash.in_(all_db_hashes)
            )
        )
        # Map by DB key (contains rule id prefix)
        existing = {c.torrent_hash: c for c in result.scalars().all()}

        # Update or create entries for matched torrents
        for torrent_hash in update_hashes:
            key = self._duration_cache_key(downloader_id, rule_id, torrent_hash)
            db_hash = self._duration_db_key(rule_id, torrent_hash)
            if db_hash in existing:
                cache = existing[db_hash]
                if cache.condition_met_since is None:
                    cache.condition_met_since = self._duration_cache.get(key, now)
            else:
                cache = TorrentCache(
                    downloader_id=downloader_id,
                    torrent_hash=db_hash,
                    name="",
                    condition_met_since=self._duration_cache.get(key, now)
                )
                self.db.add(cache)

        # Clear condition_met_since for non-matching torrents
        for torrent_hash in clear_hashes:
            key = self._duration_cache_key(downloader_id, rule_id, torrent_hash)
            if key in self._duration_cache:
                del self._duration_cache[key]
            db_hash = self._duration_db_key(rule_id, torrent_hash)
            if db_hash in existing:
                existing[db_hash].condition_met_since = None

        # Single commit for all changes
        await self.db.commit()

    async def execute_rule(
        self,
        rule: DeleteRule,
        force_execute: bool = False,
        force_delete_files: bool = False
    ) -> List[DeleteRecord]:
        """Execute a delete rule across all applicable downloaders

        Args:
            rule: The delete rule to execute
            force_execute: If True, ignore auto_delete flag on downloaders (for manual execution)
            force_delete_files: If True, always delete local files regardless of rule setting
        """
        deleted_records = []
        action_records = []

        # Get applicable downloaders
        # For manual execution (force_execute=True), don't require auto_delete to be enabled
        if rule.downloader_ids:
            if force_execute:
                result = await self.db.execute(
                    select(Downloader).where(
                        Downloader.id.in_(rule.downloader_ids),
                        Downloader.enabled == True
                    )
                )
            else:
                result = await self.db.execute(
                    select(Downloader).where(
                        Downloader.id.in_(rule.downloader_ids),
                        Downloader.enabled == True,
                        Downloader.auto_delete == True
                    )
                )
        else:
            if force_execute:
                result = await self.db.execute(
                    select(Downloader).where(
                        Downloader.enabled == True
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

        if not downloaders:
            logger.debug(f"Rule '{rule.name}': No applicable downloaders found (check auto_delete is enabled)")
            return deleted_records

        logger.debug(f"Rule '{rule.name}': Checking {len(downloaders)} downloader(s)")
        delete_count = 0

        for downloader in downloaders:
            if rule.max_delete_count > 0 and delete_count >= rule.max_delete_count:
                logger.debug(f"Rule '{rule.name}': Reached max delete count ({rule.max_delete_count})")
                break
            matching = await self.get_matching_torrents(rule, downloader)

            if matching:
                logger.info(f"Rule '{rule.name}' matched {len(matching)} torrent(s) on {downloader.name}")

            for torrent, duration_met in matching:
                # Check max delete count
                if rule.max_delete_count > 0 and delete_count >= rule.max_delete_count:
                    logger.debug(f"Rule '{rule.name}': Reached max delete count ({rule.max_delete_count})")
                    break

                # Skip if duration not met
                if not duration_met:
                    logger.debug(f"Rule '{rule.name}': Duration not met for {torrent.name[:30]}...")
                    continue

                action_taken = False
                # Determine delete_files before any action
                if force_delete_files:
                    delete_files = True
                else:
                    delete_files = rule.delete_files and not rule.only_delete_torrent

                action_type = "delete"
                if rule.limit_speed and rule.limit_speed > 0:
                    action_taken = await self._limit_torrent(
                        downloader, torrent, rule.limit_speed
                    )
                    action_type = "limit"
                elif rule.pause:
                    action_taken = await self._pause_torrent(downloader, torrent)
                    action_type = "pause"
                else:
                    action_taken = await self._delete_torrent(
                        downloader, torrent, delete_files, rule.force_report
                    )

                if action_taken:
                    delete_count += 1

                    if action_type == "delete":
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
                            action_type=action_type,
                        )
                        self.db.add(record)
                        deleted_records.append(record)
                        action_records.append(record)
                    else:
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
                            files_deleted=False,
                            reported=False,
                            action_type=action_type,
                        )
                        self.db.add(record)
                        action_records.append(record)

                    # Clear from duration cache
                    key = self._duration_cache_key(downloader.id, rule.id, torrent.hash)
                    if key in self._duration_cache:
                        del self._duration_cache[key]
                else:
                    logger.warning(f"Rule '{rule.name}': Failed to execute action on {torrent.name[:50]}")

        # Single commit for all records
        if action_records:
            await self.db.commit()

            # Send Telegram notification for batch delete
            if len(deleted_records) > 1:
                total_uploaded = sum(r.uploaded or 0 for r in deleted_records)
                try:
                    await notify_delete_batch(rule.name, len(deleted_records), total_uploaded)
                except Exception as e:
                    logger.debug(f"Failed to send batch delete notification: {e}")
            elif len(deleted_records) == 1:
                # Single delete notification
                record = deleted_records[0]
                try:
                    await notify_delete(
                        rule.name,
                        record.torrent_name,
                        record.ratio or 0,
                        record.seeding_time or 0
                    )
                except Exception as e:
                    logger.debug(f"Failed to send delete notification: {e}")

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
            async with downloader_client(downloader) as client:
                if not client:
                    logger.error(
                        f"Failed to connect to {downloader.name} for deleting {torrent.name[:30]}..."
                    )
                    return False

                # Force report before deletion
                if force_report:
                    await client.reannounce_torrent(torrent.hash)
                    # Wait a bit for report
                    import asyncio
                    await asyncio.sleep(2)

                # Delete torrent
                success = await client.remove_torrent(torrent.hash, delete_files)

            if success:
                logger.info(
                    f"Deleted torrent: {torrent.name[:50]} from {downloader.name} (files: {delete_files})"
                )
            else:
                logger.error(
                    f"Failed to delete torrent: {torrent.name[:50]} from {downloader.name}"
                )

            return success
        except Exception as e:
            logger.error(
                f"Error deleting torrent {torrent.name[:30]}... from {downloader.name}: {e}"
            )
            return False
    async def run_all_rules(self) -> List[DeleteRecord]:
        """Run all enabled delete rules"""
        result = await self.db.execute(
            select(DeleteRule)
            .where(DeleteRule.enabled == True)
            .order_by(DeleteRule.priority.desc())
        )
        rules = result.scalars().all()

        if not rules:
            logger.debug("No enabled delete rules found")
            return []

        logger.debug(f"Running {len(rules)} delete rule(s)")

        all_deleted = []
        for rule in rules:
            try:
                deleted = await self.execute_rule(rule)
                all_deleted.extend(deleted)
            except Exception as e:
                logger.error(f"Error executing rule '{rule.name}': {e}")

        return all_deleted

    async def _pause_torrent(self, downloader: Downloader, torrent: TorrentInfo) -> bool:
        try:
            async with downloader_client(downloader) as client:
                if not client:
                    return False
                success = await client.pause_torrent(torrent.hash)

            if success:
                logger.info(f"Paused torrent: {torrent.name[:50]} from {downloader.name}")
            return success
        except Exception as e:
            logger.error(f"Error pausing torrent: {e}")
            return False
    async def _limit_torrent(self, downloader: Downloader, torrent: TorrentInfo, limit_speed: int) -> bool:
        try:
            async with downloader_client(downloader) as client:
                if not client:
                    return False
                download_success = await client.set_torrent_download_limit(torrent.hash, limit_speed)
                upload_success = await client.set_torrent_upload_limit(torrent.hash, limit_speed)
                success = download_success and upload_success

            if success:
                logger.info(
                    f"Limited torrent: {torrent.name[:50]} to {limit_speed} B/s on {downloader.name}"
                )
            return success
        except Exception as e:
            logger.error(f"Error limiting torrent: {e}")
            return False
