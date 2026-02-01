import asyncio
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    User, Downloader, DeleteRecord, RssRecord,
    SpeedLimitRecord, U2MagicRecord, TorrentCache
)
from app.services.auth import get_current_user
from app.services.downloader import create_downloader
from app.utils.timezone import (
    get_local_tzinfo,
    local_day_start_utc,
    local_week_start_utc,
    local_month_start_utc,
    local_day_range_utc,
)

router = APIRouter(prefix="/statistics", tags=["Statistics"])


class PeriodStats(BaseModel):
    period: str
    start_date: datetime
    end_date: datetime
    uploaded: int = 0
    downloaded: int = 0
    deleted_count: int = 0
    deleted_size: int = 0
    rss_downloads: int = 0
    magic_downloads: int = 0


class DownloaderStats(BaseModel):
    id: int
    name: str
    type: str
    online: bool = False
    total_uploaded: int = 0
    total_downloaded: int = 0
    total_torrents: int = 0
    total_size: int = 0
    seeding_torrents: int = 0
    upload_speed: int = 0
    download_speed: int = 0
    free_space: int = 0
    deleted_count: int = 0
    deleted_size: int = 0


class OverviewStats(BaseModel):
    total_downloaders: int = 0
    online_downloaders: int = 0
    total_torrents: int = 0
    total_size: int = 0
    total_uploaded: int = 0
    total_downloaded: int = 0
    current_upload_speed: int = 0
    current_download_speed: int = 0
    total_free_space: int = 0
    today_deleted_count: int = 0
    today_deleted_size: int = 0
    today_rss_downloads: int = 0
    today_magic_downloads: int = 0
    week_deleted_count: int = 0
    week_deleted_size: int = 0
    week_rss_downloads: int = 0
    week_magic_downloads: int = 0
    month_deleted_count: int = 0
    month_deleted_size: int = 0
    month_rss_downloads: int = 0
    month_magic_downloads: int = 0


class TrendDataPoint(BaseModel):
    date: str
    uploaded: int = 0
    downloaded: int = 0
    deleted_count: int = 0
    deleted_size: int = 0
    rss_downloads: int = 0


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall statistics overview"""
    result = await db.execute(select(Downloader))
    downloaders = result.scalars().all()

    stats = OverviewStats(total_downloaders=len(downloaders))

    # Get real-time stats from downloaders (concurrent, safe connections)
    from app.services.downloader.context import downloader_client

    sem = asyncio.Semaphore(5)

    async def fetch_one(dl: Downloader):
        if not dl.enabled:
            return None
        async with sem:
            try:
                async with downloader_client(dl) as client:
                    if not client:
                        return None
                    dl_stats = await client.get_stats()
                    torrents = await client.get_torrents()
                    total_size = sum(t.size for t in torrents)
                    return dl_stats, total_size
            except Exception:
                return None

    tasks = [fetch_one(dl) for dl in downloaders if dl.enabled]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if not res or isinstance(res, Exception):
            continue
        dl_stats, total_size = res
        stats.online_downloaders += 1
        stats.total_torrents += dl_stats.total_torrents
        stats.total_uploaded += dl_stats.total_uploaded
        stats.total_downloaded += dl_stats.total_downloaded
        stats.current_upload_speed += dl_stats.upload_speed
        stats.current_download_speed += dl_stats.download_speed
        stats.total_free_space += dl_stats.free_space
        stats.total_size += total_size

    # Get period-based stats (use **local timezone** boundaries)
    now = datetime.utcnow()
    today_start = local_day_start_utc(now)
    week_start = local_week_start_utc(now)
    month_start = local_month_start_utc(now)

    # Today's stats
    today_delete = await db.execute(
        select(
            func.count(DeleteRecord.id),
            func.coalesce(func.sum(DeleteRecord.size), 0)
        ).where(DeleteRecord.deleted_at >= today_start)
    )
    row = today_delete.first()
    stats.today_deleted_count = row[0] or 0
    stats.today_deleted_size = row[1] or 0

    today_rss = await db.execute(
        select(func.count(RssRecord.id)).where(
            RssRecord.downloaded == True,
            RssRecord.created_at >= today_start
        )
    )
    stats.today_rss_downloads = today_rss.scalar() or 0

    today_magic = await db.execute(
        select(func.count(U2MagicRecord.id)).where(
            U2MagicRecord.downloaded == True,
            U2MagicRecord.created_at >= today_start
        )
    )
    stats.today_magic_downloads = today_magic.scalar() or 0

    # Week's stats
    week_delete = await db.execute(
        select(
            func.count(DeleteRecord.id),
            func.coalesce(func.sum(DeleteRecord.size), 0)
        ).where(DeleteRecord.deleted_at >= week_start)
    )
    row = week_delete.first()
    stats.week_deleted_count = row[0] or 0
    stats.week_deleted_size = row[1] or 0

    week_rss = await db.execute(
        select(func.count(RssRecord.id)).where(
            RssRecord.downloaded == True,
            RssRecord.created_at >= week_start
        )
    )
    stats.week_rss_downloads = week_rss.scalar() or 0

    week_magic = await db.execute(
        select(func.count(U2MagicRecord.id)).where(
            U2MagicRecord.downloaded == True,
            U2MagicRecord.created_at >= week_start
        )
    )
    stats.week_magic_downloads = week_magic.scalar() or 0

    # Month's stats
    month_delete = await db.execute(
        select(
            func.count(DeleteRecord.id),
            func.coalesce(func.sum(DeleteRecord.size), 0)
        ).where(DeleteRecord.deleted_at >= month_start)
    )
    row = month_delete.first()
    stats.month_deleted_count = row[0] or 0
    stats.month_deleted_size = row[1] or 0

    month_rss = await db.execute(
        select(func.count(RssRecord.id)).where(
            RssRecord.downloaded == True,
            RssRecord.created_at >= month_start
        )
    )
    stats.month_rss_downloads = month_rss.scalar() or 0

    month_magic = await db.execute(
        select(func.count(U2MagicRecord.id)).where(
            U2MagicRecord.downloaded == True,
            U2MagicRecord.created_at >= month_start
        )
    )
    stats.month_magic_downloads = month_magic.scalar() or 0

    return stats


@router.get("/downloaders", response_model=List[DownloaderStats])
async def get_downloader_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for each downloader"""
    result = await db.execute(select(Downloader))
    downloaders = result.scalars().all()

    # Batch query: deleted stats per downloader (avoid N+1 DB queries)
    delete_stats_result = await db.execute(
        select(
            DeleteRecord.downloader_id.label('downloader_id'),
            func.count(DeleteRecord.id).label('count'),
            func.coalesce(func.sum(DeleteRecord.size), 0).label('size'),
        ).group_by(DeleteRecord.downloader_id)
    )
    delete_stats_map = {
        row.downloader_id: (row.count or 0, row.size or 0)
        for row in delete_stats_result.all()
        if row.downloader_id is not None
    }

    stats_list: List[DownloaderStats] = []
    stats_by_id = {}

    for downloader in downloaders:
        stats = DownloaderStats(
            id=downloader.id,
            name=downloader.name,
            type=downloader.type.value,
        )

        d_count, d_size = delete_stats_map.get(downloader.id, (0, 0))
        stats.deleted_count = d_count
        stats.deleted_size = d_size

        stats_list.append(stats)
        stats_by_id[downloader.id] = stats

    # Get real-time stats concurrently (network-bound)
    from app.services.downloader.context import downloader_client

    sem = asyncio.Semaphore(5)

    async def fetch_realtime(dl: Downloader):
        if not dl.enabled:
            return dl.id, None
        async with sem:
            try:
                async with downloader_client(dl) as client:
                    if not client:
                        return dl.id, None
                    dl_stats = await client.get_stats()
                    torrents = await client.get_torrents()
                    total_size = sum(t.size for t in torrents)
                    return dl.id, (dl_stats, total_size)
            except Exception:
                return dl.id, None

    realtime_tasks = [fetch_realtime(dl) for dl in downloaders if dl.enabled]
    realtime_results = await asyncio.gather(*realtime_tasks, return_exceptions=True)

    for res in realtime_results:
        if not res or isinstance(res, Exception):
            continue
        dl_id, payload = res
        if not payload:
            continue
        dl_stats, total_size = payload
        stats = stats_by_id.get(dl_id)
        if not stats:
            continue

        stats.online = True
        stats.total_uploaded = dl_stats.total_uploaded
        stats.total_downloaded = dl_stats.total_downloaded
        stats.total_torrents = dl_stats.total_torrents
        stats.seeding_torrents = dl_stats.seeding_torrents
        stats.upload_speed = dl_stats.upload_speed
        stats.download_speed = dl_stats.download_speed
        stats.free_space = dl_stats.free_space
        stats.total_size = total_size

    return stats_list


@router.get("/trend", response_model=List[TrendDataPoint])
async def get_trend_data(
    days: int = Query(default=7, ge=1, le=90),
    downloader_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trend data for charts - optimized with batch queries"""
    # Use **local timezone** day boundaries.
    now = datetime.utcnow()
    start_date, end_date = local_day_range_utc(days, now)

    # Initialize trend data dict for all local dates in range
    # Use pure date arithmetic to avoid DST issues when adding timedeltas to timezone-aware datetimes.
    tz = get_local_tzinfo()
    start_local_date = start_date.replace(tzinfo=timezone.utc).astimezone(tz).date()

    trend_dict = {}
    for i in range(days):
        date_str = (start_local_date + timedelta(days=i)).isoformat()
        trend_dict[date_str] = TrendDataPoint(date=date_str)

    # Batch query: Deleted stats grouped by date
    delete_query = select(
        func.date(DeleteRecord.deleted_at, 'localtime').label('date'),
        func.count(DeleteRecord.id).label('count'),
        func.coalesce(func.sum(DeleteRecord.size), 0).label('size')
    ).where(
        DeleteRecord.deleted_at >= start_date,
        DeleteRecord.deleted_at < end_date
    ).group_by(func.date(DeleteRecord.deleted_at, 'localtime'))

    if downloader_id:
        delete_query = delete_query.where(DeleteRecord.downloader_id == downloader_id)

    delete_result = await db.execute(delete_query)
    for row in delete_result.all():
        date_str = str(row.date)
        if date_str in trend_dict:
            trend_dict[date_str].deleted_count = row.count or 0
            trend_dict[date_str].deleted_size = row.size or 0

    # Batch query: RSS downloads grouped by date
    rss_query = select(
        func.date(RssRecord.created_at, 'localtime').label('date'),
        func.count(RssRecord.id).label('count')
    ).where(
        RssRecord.downloaded == True,
        RssRecord.created_at >= start_date,
        RssRecord.created_at < end_date
    ).group_by(func.date(RssRecord.created_at, 'localtime'))

    rss_result = await db.execute(rss_query)
    for row in rss_result.all():
        date_str = str(row.date)
        if date_str in trend_dict:
            trend_dict[date_str].rss_downloads = row.count or 0

    # Batch query: Speed limit records grouped by date
    speed_query = select(
        func.date(SpeedLimitRecord.created_at, 'localtime').label('date'),
        func.coalesce(func.sum(SpeedLimitRecord.uploaded), 0).label('uploaded'),
        func.coalesce(func.sum(SpeedLimitRecord.downloaded), 0).label('downloaded')
    ).where(
        SpeedLimitRecord.created_at >= start_date,
        SpeedLimitRecord.created_at < end_date
    ).group_by(func.date(SpeedLimitRecord.created_at, 'localtime'))

    if downloader_id:
        speed_query = speed_query.where(SpeedLimitRecord.downloader_id == downloader_id)

    speed_result = await db.execute(speed_query)
    for row in speed_result.all():
        date_str = str(row.date)
        if date_str in trend_dict:
            trend_dict[date_str].uploaded = row.uploaded or 0
            trend_dict[date_str].downloaded = row.downloaded or 0

    # Return sorted list
    return [trend_dict[k] for k in sorted(trend_dict.keys())]


@router.get("/period", response_model=List[PeriodStats])
async def get_period_stats(
    period: str = Query(default="daily", regex="^(daily|weekly|monthly)$"),
    count: int = Query(default=7, ge=1, le=30),
    downloader_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics grouped by period (daily/weekly/monthly)"""
    # Use local timezone boundaries for period grouping
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    tz = get_local_tzinfo()
    today_local = now_utc.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    periods = []

    for i in range(count):
        # Compute period boundaries in local timezone first, then convert to UTC for DB filtering.
        if period == "daily":
            start_local = today_local - timedelta(days=i)
            end_local = start_local + timedelta(days=1)
            period_name = start_local.strftime("%Y-%m-%d")
        elif period == "weekly":
            week_start_local = today_local - timedelta(days=today_local.weekday())
            start_local = week_start_local - timedelta(weeks=i)
            end_local = start_local + timedelta(weeks=1)
            period_name = f"Week {start_local.strftime('%Y-%m-%d')}"
        else:  # monthly
            month_start_local = today_local.replace(day=1)
            # Go back i months
            for _ in range(i):
                month_start_local = (month_start_local - timedelta(days=1)).replace(day=1)
            start_local = month_start_local
            # Calculate end of month
            if month_start_local.month == 12:
                end_local = month_start_local.replace(year=month_start_local.year + 1, month=1)
            else:
                end_local = month_start_local.replace(month=month_start_local.month + 1)
            period_name = start_local.strftime("%Y-%m")

        start = start_local.astimezone(timezone.utc).replace(tzinfo=None)
        end = end_local.astimezone(timezone.utc).replace(tzinfo=None)

        stats = PeriodStats(
            period=period_name,
            start_date=start,
            end_date=end
        )

        # Deleted stats
        delete_query = select(
            func.count(DeleteRecord.id),
            func.coalesce(func.sum(DeleteRecord.size), 0)
        ).where(
            DeleteRecord.deleted_at >= start,
            DeleteRecord.deleted_at < end
        )
        if downloader_id:
            delete_query = delete_query.where(DeleteRecord.downloader_id == downloader_id)

        delete_result = await db.execute(delete_query)
        row = delete_result.first()
        stats.deleted_count = row[0] or 0
        stats.deleted_size = row[1] or 0

        # RSS downloads
        rss_result = await db.execute(
            select(func.count(RssRecord.id)).where(
                RssRecord.downloaded == True,
                RssRecord.created_at >= start,
                RssRecord.created_at < end
            )
        )
        stats.rss_downloads = rss_result.scalar() or 0

        # Magic downloads
        magic_result = await db.execute(
            select(func.count(U2MagicRecord.id)).where(
                U2MagicRecord.downloaded == True,
                U2MagicRecord.created_at >= start,
                U2MagicRecord.created_at < end
            )
        )
        stats.magic_downloads = magic_result.scalar() or 0

        # Speed records for upload/download
        speed_query = select(
            func.coalesce(func.sum(SpeedLimitRecord.uploaded), 0),
            func.coalesce(func.sum(SpeedLimitRecord.downloaded), 0)
        ).where(
            SpeedLimitRecord.created_at >= start,
            SpeedLimitRecord.created_at < end
        )
        if downloader_id:
            speed_query = speed_query.where(SpeedLimitRecord.downloader_id == downloader_id)

        speed_result = await db.execute(speed_query)
        row = speed_result.first()
        stats.uploaded = row[0] or 0
        stats.downloaded = row[1] or 0

        periods.append(stats)

    # Reverse so newest is last
    periods.reverse()

    return periods


@router.get("/delete-summary")
async def get_delete_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of deleted torrents"""
    since = datetime.utcnow() - timedelta(days=days)

    # Overall stats
    overall = await db.execute(
        select(
            func.count(DeleteRecord.id),
            func.coalesce(func.sum(DeleteRecord.size), 0),
            func.coalesce(func.avg(DeleteRecord.ratio), 0),
            func.coalesce(func.avg(DeleteRecord.seeding_time), 0)
        ).where(DeleteRecord.deleted_at >= since)
    )
    row = overall.first()

    # By rule
    by_rule = await db.execute(
        select(
            DeleteRecord.rule_name,
            func.count(DeleteRecord.id).label('count'),
            func.coalesce(func.sum(DeleteRecord.size), 0).label('size')
        ).where(
            DeleteRecord.deleted_at >= since
        ).group_by(DeleteRecord.rule_name).order_by(desc('count'))
    )
    rules_stats = [
        {"rule_name": r[0], "count": r[1], "size": r[2]}
        for r in by_rule.all()
    ]

    # By downloader
    by_downloader = await db.execute(
        select(
            DeleteRecord.downloader_name,
            func.count(DeleteRecord.id).label('count'),
            func.coalesce(func.sum(DeleteRecord.size), 0).label('size')
        ).where(
            DeleteRecord.deleted_at >= since
        ).group_by(DeleteRecord.downloader_name).order_by(desc('count'))
    )
    downloader_stats = [
        {"downloader_name": r[0], "count": r[1], "size": r[2]}
        for r in by_downloader.all()
    ]

    return {
        "period_days": days,
        "total_count": row[0] or 0,
        "total_size": row[1] or 0,
        "avg_ratio": round(row[2] or 0, 2),
        "avg_seeding_time_hours": round((row[3] or 0) / 3600, 1),
        "by_rule": rules_stats,
        "by_downloader": downloader_stats
    }


@router.get("/rss-summary")
async def get_rss_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get summary of RSS downloads"""
    since = datetime.utcnow() - timedelta(days=days)

    # Overall stats
    overall = await db.execute(
        select(func.count(RssRecord.id)).where(
            RssRecord.downloaded == True,
            RssRecord.created_at >= since
        )
    )
    total_downloads = overall.scalar() or 0

    # By feed
    from app.models import RssFeed
    by_feed = await db.execute(
        select(
            RssFeed.name,
            func.count(RssRecord.id).label('count')
        ).join(
            RssFeed, RssRecord.feed_id == RssFeed.id
        ).where(
            RssRecord.downloaded == True,
            RssRecord.created_at >= since
        ).group_by(RssFeed.name).order_by(desc('count'))
    )
    feed_stats = [
        {"feed_name": r[0], "count": r[1]}
        for r in by_feed.all()
    ]

    # Daily trend (local timezone)
    daily_trend = []
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    tz = get_local_tzinfo()
    today_local = now_utc.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(min(days, 14)):
        day_local = today_local - timedelta(days=i)
        next_day_local = day_local + timedelta(days=1)
        day = day_local.astimezone(timezone.utc).replace(tzinfo=None)
        next_day = next_day_local.astimezone(timezone.utc).replace(tzinfo=None)

        count_result = await db.execute(
            select(func.count(RssRecord.id)).where(
                RssRecord.downloaded == True,
                RssRecord.created_at >= day,
                RssRecord.created_at < next_day
            )
        )
        daily_trend.append({
            "date": day_local.strftime("%Y-%m-%d"),
            "count": count_result.scalar() or 0
        })

    daily_trend.reverse()

    return {
        "period_days": days,
        "total_downloads": total_downloads,
        "by_feed": feed_stats,
        "daily_trend": daily_trend
    }
