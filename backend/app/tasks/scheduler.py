import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, delete

from app.config import settings
from app.database import async_session_maker
from app.models import (
    RssFeed, Downloader, SpeedLimitConfig, U2MagicConfig, DeleteRule,
    SpeedLimitRecord, DeleteRecord, RssRecord, U2MagicRecord, SystemSettings,
    NetcupConfig, NetcupRecord
)
from app.services.rss_service import RssService
from app.services.delete_service import DeleteService
from app.services.speed_limiter import SpeedLimiterService
from app.services.u2_magic import U2MagicService
from app.services.netcup_monitor import netcup_monitor_service
from app.services.downloader import create_downloader
from app.utils import get_logger

logger = get_logger('pt_manager.scheduler')

# Configuration constants
RSS_CHECK_INTERVAL_SECONDS = 60
DELETE_CHECK_INTERVAL_SECONDS = 60
SPEED_LIMIT_INTERVAL_SECONDS = 5  # 默认间隔，动态调整时作为上限
SPEED_LIMIT_MIN_INTERVAL = 0.2    # 动态间隔下限（200ms）
U2_MAGIC_INTERVAL_SECONDS = 60
AUTO_REPORT_INTERVAL_SECONDS = 60
CACHE_UPDATE_INTERVAL_SECONDS = 30
RECORD_CLEANUP_INTERVAL_HOURS = 6
RECORD_RETENTION_DAYS = 30
NETCUP_CHECK_INTERVAL_SECONDS = 60


class TaskScheduler:
    """Central task scheduler for all background jobs"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                'coalesce': settings.SCHEDULER_JOB_COALESCE,
                'max_instances': settings.SCHEDULER_JOB_MAX_INSTANCES,
                'misfire_grace_time': settings.SCHEDULER_MISFIRE_GRACE_TIME,
            }
        )
        self._jobs: Dict[str, str] = {}  # job_name -> job_id
        self._running = False
        # Shared service instances to avoid repeated creation
        self._speed_limiter: Optional[SpeedLimiterService] = None
        # 动态限速循环任务
        self._speed_limit_task: Optional[asyncio.Task] = None
        self._speed_limit_enabled = False
        self._speed_limit_lock = asyncio.Lock()

    def start(self):
        """Start the scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Task scheduler started")

            # Add default jobs
            asyncio.create_task(self._setup_default_jobs())

    def stop(self):
        """Stop the scheduler"""
        if self._running:
            # 停止限速循环
            self._stop_speed_limit_loop()
            self.scheduler.shutdown()
            self._running = False
            logger.info("Task scheduler stopped")

    async def _setup_default_jobs(self):
        """Setup default scheduled jobs"""
        # RSS feed checking
        self.add_job(
            "rss_check",
            self._run_rss_check,
            IntervalTrigger(seconds=RSS_CHECK_INTERVAL_SECONDS),
        )

        # Delete rule checking
        delete_interval = await self._get_delete_interval()
        self.add_job(
            "delete_check",
            self._run_delete_check,
            IntervalTrigger(seconds=delete_interval),
        )

        # Speed limit control - 使用动态间隔的循环任务
        # 不再使用固定间隔的 APScheduler 任务，而是启动一个动态循环
        self._start_speed_limit_loop()

        # U2 magic checking
        self.add_job(
            "u2_magic",
            self._run_u2_magic,
            IntervalTrigger(seconds=U2_MAGIC_INTERVAL_SECONDS),
        )

        # Auto report for new torrents
        self.add_job(
            "auto_report",
            self._run_auto_report,
            IntervalTrigger(seconds=AUTO_REPORT_INTERVAL_SECONDS),
        )

        # Record cleanup task (run every 6 hours)
        self.add_job(
            "record_cleanup",
            self._run_record_cleanup,
            IntervalTrigger(hours=RECORD_CLEANUP_INTERVAL_HOURS),
        )

        # Netcup throttle monitoring
        self.add_job(
            "netcup_check",
            self._run_netcup_check,
            IntervalTrigger(seconds=NETCUP_CHECK_INTERVAL_SECONDS),
        )

        logger.info("Default jobs configured")

    async def _get_delete_interval(self) -> int:
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(SystemSettings).where(SystemSettings.key == "delete_check_interval_seconds")
                )
                setting = result.scalar_one_or_none()
                if setting and setting.value:
                    return max(5, int(setting.value))
        except Exception as e:
            logger.error(f"Failed to load delete interval: {e}")
        return DELETE_CHECK_INTERVAL_SECONDS

    def add_job(self, name: str, func, trigger, **kwargs):
        """Add or replace a job"""
        if name in self._jobs:
            self.scheduler.remove_job(self._jobs[name])

        # Safe defaults: avoid overlapping jobs and catch up bursts
        kwargs.setdefault('max_instances', settings.SCHEDULER_JOB_MAX_INSTANCES)
        kwargs.setdefault('coalesce', settings.SCHEDULER_JOB_COALESCE)
        kwargs.setdefault('misfire_grace_time', settings.SCHEDULER_MISFIRE_GRACE_TIME)

        job = self.scheduler.add_job(func, trigger, **kwargs)
        self._jobs[name] = job.id

    def remove_job(self, name: str):
        """Remove a job"""
        if name in self._jobs:
            self.scheduler.remove_job(self._jobs[name])
            del self._jobs[name]

    def set_delete_interval(self, seconds: int):
        """Update delete rule check interval in seconds."""
        self.add_job(
            "delete_check",
            self._run_delete_check,
            IntervalTrigger(seconds=seconds),
        )

    async def _run_rss_check(self):
        """Run RSS feed checking"""
        try:
            async with async_session_maker() as db:
                # Get enabled feeds that need checking
                result = await db.execute(
                    select(RssFeed).where(RssFeed.enabled == True)
                )
                feeds = result.scalars().all()

                if not feeds:
                    logger.debug("No enabled RSS feeds found")
                    return

                logger.info(f"Checking {len(feeds)} RSS feed(s)...")
                now = datetime.utcnow()
                # Create service once for all feeds
                service = RssService(db)

                # Filter feeds that are due for checking
                feeds_to_process = []
                for feed in feeds:
                    if feed.last_fetch:
                        next_fetch = feed.last_fetch + timedelta(seconds=feed.fetch_interval)
                        if now < next_fetch:
                            logger.debug(f"RSS feed '{feed.name}' not due yet, next fetch at {next_fetch}")
                            continue
                    feeds_to_process.append(feed)

                if not feeds_to_process:
                    return

                # Process feeds in parallel with concurrency limit
                async def process_single_feed(feed):
                    try:
                        records = await service.process_feed(feed)
                        if records:
                            downloaded = sum(1 for r in records if r.downloaded)
                            logger.info(f"RSS feed '{feed.name}': {len(records)} new, {downloaded} downloaded")
                        return records
                    except Exception as e:
                        logger.error(f"Error processing RSS feed '{feed.name}': {type(e).__name__}: {e}")
                        return []

                # Process all feeds concurrently
                await asyncio.gather(*[process_single_feed(f) for f in feeds_to_process])
        except Exception as e:
            logger.error(f"RSS check error: {type(e).__name__}: {e}")

    async def _run_delete_check(self):
        """Run delete rule checking"""
        try:
            async with async_session_maker() as db:
                service = DeleteService(db)
                deleted = await service.run_all_rules()
                if deleted:
                    logger.info(f"Deleted {len(deleted)} torrents")
        except Exception as e:
            logger.error(f"Delete check error: {e}")

    def _start_speed_limit_loop(self):
        """启动动态间隔的限速循环任务"""
        # Use a flag to prevent multiple concurrent starts
        if self._speed_limit_task is None or self._speed_limit_task.done():
            self._speed_limit_enabled = True
            self._speed_limit_task = asyncio.create_task(self._speed_limit_loop_wrapper())
            logger.info("动态限速循环任务已启动")

    def _stop_speed_limit_loop(self):
        """停止限速循环任务"""
        self._speed_limit_enabled = False
        if self._speed_limit_task and not self._speed_limit_task.done():
            self._speed_limit_task.cancel()
            logger.info("动态限速循环任务已停止")

    async def _speed_limit_loop_wrapper(self):
        """Wrapper to ensure only one loop runs at a time using a lock"""
        async with self._speed_limit_lock:
            await self._speed_limit_loop_inner()

    async def _speed_limit_loop_inner(self):
        """动态间隔的限速循环

        根据种子的剩余汇报时间动态调整检查频率：
        - 剩余 ≤5秒: 200ms
        - 剩余 ≤15秒: 500ms
        - 剩余 ≤30秒: 1秒
        - 剩余 ≤60秒: 2秒
        - 剩余 ≤120秒: 3秒
        - 剩余 >120秒: 5秒
        """
        logger.info("动态限速循环开始运行")
        last_interval = SPEED_LIMIT_INTERVAL_SECONDS

        while self._speed_limit_enabled and self._running:
            try:
                # 执行限速检查
                suggested_interval = await self._run_speed_limit()

                # 使用建议的间隔，但确保在合理范围内
                if suggested_interval is not None:
                    interval = max(SPEED_LIMIT_MIN_INTERVAL, min(suggested_interval, SPEED_LIMIT_INTERVAL_SECONDS))
                else:
                    interval = SPEED_LIMIT_INTERVAL_SECONDS

                # 如果间隔变化较大，记录日志
                if abs(interval - last_interval) > 0.5:
                    logger.debug(f"限速检查间隔调整: {last_interval:.1f}s -> {interval:.1f}s")
                last_interval = interval

                # 等待指定间隔
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("限速循环被取消")
                break
            except Exception as e:
                logger.error(f"限速循环异常: {e}")
                await asyncio.sleep(SPEED_LIMIT_INTERVAL_SECONDS)  # 出错时使用默认间隔

        logger.info("动态限速循环已结束")

    async def _run_speed_limit(self) -> Optional[float]:
        """Run speed limit control

        Returns:
            建议的下次检查间隔（秒），如果未启用则返回 None
        """
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(SpeedLimitConfig).limit(1))
                config = result.scalar_one_or_none()

                if config and config.enabled:
                    # Reuse speed limiter service to preserve state (Kalman, PID)
                    if self._speed_limiter is None:
                        self._speed_limiter = SpeedLimiterService(db)
                        await self._speed_limiter.load_state()  # 首次创建时加载已保存的状态
                    else:
                        self._speed_limiter.db = db

                    results = await self._speed_limiter.apply_limits()
                    if results:
                        logger.debug(f"Speed limits applied to {len(results)} trackers")

                    # 获取建议的下次检查间隔
                    return self._speed_limiter.get_suggested_interval()
                elif self._speed_limiter:
                    # Clear limits if disabled
                    self._speed_limiter.db = db
                    await self._speed_limiter.clear_limits()
                    self._speed_limiter = None
                    return None
        except Exception as e:
            logger.error(f"Speed limit error: {e}")
        return SPEED_LIMIT_INTERVAL_SECONDS  # 出错时返回默认间隔

    async def _run_u2_magic(self):
        """Run U2 magic checking"""
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(U2MagicConfig).limit(1))
                config = result.scalar_one_or_none()

                if config and config.enabled:
                    service = U2MagicService(db)
                    try:
                        result = await service.process_magic()
                    finally:
                        await service.close()
                    if result:
                        total = result.get("total", 0)
                        downloaded = result.get("downloaded", 0)
                        logger.info(f"U2 magic: {total} found, {downloaded} downloaded")
        except Exception as e:
            logger.error(f"U2 magic error: {e}")

    async def _run_auto_report(self):
        """Auto report torrents that were added 5 minutes ago"""
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Downloader).where(
                        Downloader.enabled == True,
                        Downloader.auto_report == True
                    )
                )
                downloaders = result.scalars().all()

                now = datetime.now()
                report_window_start = timedelta(minutes=4, seconds=30)
                report_window_end = timedelta(minutes=5, seconds=30)

                for downloader in downloaders:
                    try:
                        client = create_downloader(downloader)
                        if not await client.connect():
                            continue

                        reported_count = 0
                        try:
                            torrents = await client.get_torrents()

                            for torrent in torrents:
                                if torrent.added_time:
                                    age = now - torrent.added_time
                                    # Report torrents added ~5 minutes ago
                                    if report_window_start < age < report_window_end:
                                        await client.reannounce_torrent(torrent.hash)
                                        reported_count += 1
                        finally:
                            await client.disconnect()

                        if reported_count > 0:
                            logger.info(f"Auto reported {reported_count} torrents from {downloader.name}")
                    except Exception as e:
                        logger.error(f"Auto report error for {downloader.name}: {e}")
        except Exception as e:
            logger.error(f"Auto report error: {e}")

    async def _run_record_cleanup(self):
        """Clean up old records to prevent database bloat"""
        try:
            async with async_session_maker() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=RECORD_RETENTION_DAYS)

                # Clean up speed limit records (keep only last 30 days)
                await db.execute(
                    delete(SpeedLimitRecord).where(SpeedLimitRecord.created_at < cutoff_date)
                )

                # Clean up old RSS records that weren't downloaded
                await db.execute(
                    delete(RssRecord).where(
                        RssRecord.created_at < cutoff_date,
                        RssRecord.downloaded == False
                    )
                )

                # Clean up delete records
                await db.execute(
                    delete(DeleteRecord).where(DeleteRecord.deleted_at < cutoff_date)
                )

                # Clean up old U2 magic records that weren't downloaded
                await db.execute(
                    delete(U2MagicRecord).where(
                        U2MagicRecord.created_at < cutoff_date,
                        U2MagicRecord.downloaded == False
                    )
                )

                await db.commit()
                logger.info(f"Cleaned up records older than {RECORD_RETENTION_DAYS} days")
        except Exception as e:
            logger.error(f"Record cleanup error: {e}")

    async def _run_netcup_check(self):
        """Run Netcup throttle status check"""
        try:
            config = await netcup_monitor_service.get_config()
            if config and config.enabled:
                results = await netcup_monitor_service.run_check()
                if results:
                    throttled = sum(1 for r in results.values() if r.get("status") == "throttled")
                    if throttled > 0:
                        logger.warning(f"Netcup: {throttled}/{len(results)} servers throttled")
                    else:
                        logger.debug(f"Netcup: all {len(results)} servers normal")
        except Exception as e:
            logger.error(f"Netcup check error: {e}")


# Global scheduler instance
scheduler = TaskScheduler()


def get_scheduler() -> TaskScheduler:
    return scheduler