from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    User, Downloader, RssRecord, DeleteRecord, U2MagicRecord,
    SpeedLimitConfig, U2MagicConfig
)
from app.schemas import DashboardStats, TimelineItem
from app.services.auth import get_current_user
from app.services.downloader import create_downloader

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics"""
    result = await db.execute(
        select(Downloader).where(Downloader.enabled == True)
    )
    downloaders = result.scalars().all()

    total_upload_speed = 0
    total_download_speed = 0
    total_uploaded = 0
    total_downloaded = 0
    active_torrents = 0
    seeding_torrents = 0
    downloading_torrents = 0
    total_torrents = 0
    total_size = 0
    free_space = 0

    for downloader in downloaders:
        try:
            client = create_downloader(downloader)
            if await client.connect():
                stats = await client.get_stats()
                torrents = await client.get_torrents()
                await client.disconnect()

                total_upload_speed += stats.upload_speed
                total_download_speed += stats.download_speed
                total_uploaded += stats.total_uploaded
                total_downloaded += stats.total_downloaded
                active_torrents += stats.active_torrents
                seeding_torrents += stats.seeding_torrents
                downloading_torrents += stats.downloading_torrents
                total_torrents += stats.total_torrents
                free_space += stats.free_space

                for t in torrents:
                    total_size += t.size
        except Exception as e:
            print(f"Error getting stats for {downloader.name}: {e}")

    return DashboardStats(
        total_upload_speed=total_upload_speed,
        total_download_speed=total_download_speed,
        total_uploaded=total_uploaded,
        total_downloaded=total_downloaded,
        active_torrents=active_torrents,
        seeding_torrents=seeding_torrents,
        downloading_torrents=downloading_torrents,
        total_torrents=total_torrents,
        total_size=total_size,
        free_space=free_space,
    )


@router.get("/timeline", response_model=List[TimelineItem])
async def get_timeline(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity timeline"""
    timeline = []

    # Get recent RSS records
    rss_result = await db.execute(
        select(RssRecord)
        .where(RssRecord.downloaded == True)
        .order_by(desc(RssRecord.created_at))
        .limit(limit)
    )
    for record in rss_result.scalars().all():
        timeline.append(TimelineItem(
            id=record.id,
            type="rss",
            title=f"RSS: {record.title[:50]}...",
            description=f"Downloaded from feed",
            timestamp=record.created_at,
        ))

    # Get recent delete records
    delete_result = await db.execute(
        select(DeleteRecord)
        .order_by(desc(DeleteRecord.deleted_at))
        .limit(limit)
    )
    for record in delete_result.scalars().all():
        timeline.append(TimelineItem(
            id=record.id,
            type="delete",
            title=f"Deleted: {record.torrent_name[:50]}...",
            description=f"Rule: {record.rule_name}, Ratio: {record.ratio:.2f}",
            timestamp=record.deleted_at,
        ))

    # Get recent U2 magic records
    magic_result = await db.execute(
        select(U2MagicRecord)
        .where(U2MagicRecord.downloaded == True)
        .order_by(desc(U2MagicRecord.created_at))
        .limit(limit)
    )
    for record in magic_result.scalars().all():
        timeline.append(TimelineItem(
            id=record.id,
            type="magic",
            title=f"U2 Magic: {record.torrent_name[:50]}...",
            description=f"Type: {record.magic_type}",
            timestamp=record.created_at,
        ))

    # Sort by timestamp and limit
    timeline.sort(key=lambda x: x.timestamp, reverse=True)
    return timeline[:limit]


@router.get("/downloaders-status")
async def get_downloaders_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of all downloaders"""
    result = await db.execute(select(Downloader))
    downloaders = result.scalars().all()

    statuses = []
    for downloader in downloaders:
        status = {
            "id": downloader.id,
            "name": downloader.name,
            "type": downloader.type.value,
            "enabled": downloader.enabled,
            "online": False,
            "upload_speed": 0,
            "download_speed": 0,
            "free_space": 0,
            "total_torrents": 0,
        }

        if downloader.enabled:
            try:
                client = create_downloader(downloader)
                if await client.connect():
                    stats = await client.get_stats()
                    await client.disconnect()

                    status["online"] = True
                    status["upload_speed"] = stats.upload_speed
                    status["download_speed"] = stats.download_speed
                    status["free_space"] = stats.free_space
                    status["total_torrents"] = stats.total_torrents
            except Exception:
                pass

        statuses.append(status)

    return statuses


@router.get("/services-status")
async def get_services_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of all services"""
    # Speed limit status
    speed_result = await db.execute(select(SpeedLimitConfig).limit(1))
    speed_config = speed_result.scalar_one_or_none()

    # U2 magic status
    u2_result = await db.execute(select(U2MagicConfig).limit(1))
    u2_config = u2_result.scalar_one_or_none()

    # RSS feeds count
    from app.models import RssFeed, DeleteRule
    rss_result = await db.execute(
        select(func.count(RssFeed.id)).where(RssFeed.enabled == True)
    )
    rss_count = rss_result.scalar() or 0

    # Delete rules count
    delete_result = await db.execute(
        select(func.count(DeleteRule.id)).where(DeleteRule.enabled == True)
    )
    delete_count = delete_result.scalar() or 0

    return {
        "speed_limit": {
            "enabled": speed_config.enabled if speed_config else False,
            "target_speed": speed_config.target_upload_speed if speed_config else 0,
        },
        "u2_magic": {
            "enabled": u2_config.enabled if u2_config else False,
        },
        "rss": {
            "enabled_feeds": rss_count,
        },
        "delete": {
            "enabled_rules": delete_count,
        },
    }


@router.get("/recent-activity")
async def get_recent_activity(
    hours: int = 24,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activity summary"""
    since = datetime.utcnow() - timedelta(hours=hours)

    # RSS downloads
    rss_result = await db.execute(
        select(func.count(RssRecord.id)).where(
            RssRecord.downloaded == True,
            RssRecord.created_at >= since
        )
    )
    rss_downloads = rss_result.scalar() or 0

    # Deleted torrents
    delete_result = await db.execute(
        select(func.count(DeleteRecord.id)).where(
            DeleteRecord.deleted_at >= since
        )
    )
    deleted_count = delete_result.scalar() or 0

    # U2 magic downloads
    magic_result = await db.execute(
        select(func.count(U2MagicRecord.id)).where(
            U2MagicRecord.downloaded == True,
            U2MagicRecord.created_at >= since
        )
    )
    magic_downloads = magic_result.scalar() or 0

    return {
        "period_hours": hours,
        "rss_downloads": rss_downloads,
        "deleted_torrents": deleted_count,
        "magic_downloads": magic_downloads,
    }
