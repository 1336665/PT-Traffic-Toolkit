import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, delete

from app.database import async_session_maker
from app.models import (
    RssFeed, Downloader, SpeedLimitConfig, U2MagicConfig, DeleteRule,
    SpeedLimitRecord, DeleteRecord, RssRecord, U2MagicRecord, SystemSettings
)
from app.services.rss_service import RssService
from app.services.delete_service import DeleteService
from app.services.speed_limiter import SpeedLimiterService
from app.services.u2_magic import U2MagicService
from app.services.downloader import create_downloader
from app.utils import get_logger

logger = get_logger('pt_manager.scheduler')

# Configuration constants
RSS_CHECK_INTERVAL_SECONDS = 60
DELETE_CHECK_INTERVAL_SECONDS = 60
SPEED_LIMIT_INTERVAL_SECONDS = 10
U2_MAGIC_INTERVAL_SECONDS = 60
AUTO_REPORT_INTERVAL_SECONDS = 60
CACHE_UPDATE_INTERVAL_SECONDS = 30
RECORD_CLEANUP_INTERVAL_HOURS = 6
RECORD_RETENTION_DAYS = 30


class TaskScheduler:
    """Central task scheduler for all background jobs"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs: Dict[str, str] = {}  # job_name -> job_id
        self._running = False
        # Shared service instances to avoid repeated creation
        self._speed_limiter: Optional[SpeedLimiterService] = None

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

        # Speed limit control
        self.add_job(
            "speed_limit",
            self._run_speed_limit,
            IntervalTrigger(seconds=SPEED_LIMIT_INTERVAL_SECONDS),
        )

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

                for feed in feeds:
                    # Check if it's time to fetch this feed
                    if feed.last_fetch:
                        next_fetch = feed.last_fetch + timedelta(seconds=feed.fetch_interval)
                        if now < next_fetch:
                            logger.debug(f"RSS feed '{feed.name}' not due yet, next fetch at {next_fetch}")
                            continue

                    # Process feed
                    try:
                        records = await service.process_feed(feed)
                        if records:
                            downloaded = sum(1 for r in records if r.downloaded)
                            logger.info(f"RSS feed '{feed.name}': {len(records)} new, {downloaded} downloaded")
                    except Exception as e:
                        logger.error(f"Error processing RSS feed '{feed.name}': {type(e).__name__}: {e}")
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

    async def _run_speed_limit(self):
        """Run speed limit control"""
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(SpeedLimitConfig).limit(1))
                config = result.scalar_one_or_none()

                if config and config.enabled:
                    # Reuse speed limiter service to preserve state (Kalman, PID)
                    if self._speed_limiter is None:
                        self._speed_limiter = SpeedLimiterService(db)
                    else:
                        self._speed_limiter.db = db

                    results = await self._speed_limiter.apply_limits()
                    if results:
                        logger.debug(f"Speed limits applied to {len(results)} trackers")
                elif self._speed_limiter:
                    # Clear limits if disabled
                    self._speed_limiter.db = db
                    await self._speed_limiter.clear_limits()
                    self._speed_limiter = None
        except Exception as e:
            logger.error(f"Speed limit error: {e}")

    async def _run_u2_magic(self):
        """Run U2 magic checking"""
        try:
            async with async_session_maker() as db:
                result = await db.execute(select(U2MagicConfig).limit(1))
                config = result.scalar_one_or_none()

                if config and config.enabled:
                    service = U2MagicService(db)
                    result = await service.process_magic()
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

                now = datetime.utcnow()
                report_window_start = timedelta(minutes=4, seconds=30)
                report_window_end = timedelta(minutes=5, seconds=30)

                for downloader in downloaders:
                    try:
                        client = create_downloader(downloader)
                        if not await client.connect():
                            continue

                        torrents = await client.get_torrents()
                        reported_count = 0

                        for torrent in torrents:
                            if torrent.added_time:
                                age = now - torrent.added_time
                                # Report torrents added ~5 minutes ago
                                if report_window_start < age < report_window_end:
                                    await client.reannounce_torrent(torrent.hash)
                                    reported_count += 1

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


# Global scheduler instance
scheduler = TaskScheduler()


def get_scheduler() -> TaskScheduler:
    return scheduler
