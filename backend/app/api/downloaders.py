import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Downloader
from app.schemas import (
    DownloaderCreate,
    DownloaderUpdate,
    DownloaderResponse,
    DownloaderStatus,
    TorrentInfo,
)
from app.services.auth import get_current_user
from app.services.downloader import create_downloader
from app.utils import get_logger

logger = get_logger('pt_manager.downloaders')
router = APIRouter(prefix="/downloaders", tags=["Downloaders"])


@router.get("", response_model=List[DownloaderResponse])
async def get_downloaders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all downloaders"""
    result = await db.execute(select(Downloader).order_by(Downloader.id))
    return result.scalars().all()


@router.get("/status/all", response_model=List[DownloaderStatus])
async def get_all_downloaders_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of all downloaders in parallel for better performance"""
    result = await db.execute(select(Downloader).order_by(Downloader.id))
    downloaders = result.scalars().all()

    async def get_single_status(downloader: Downloader) -> DownloaderStatus:
        """Get status for a single downloader"""
        try:
            client = create_downloader(downloader)
            try:
                if await client.connect():
                    stats = await client.get_stats()
                    return DownloaderStatus(
                        id=downloader.id,
                        name=downloader.name,
                        online=True,
                        upload_speed=stats.upload_speed,
                        download_speed=stats.download_speed,
                        free_space=stats.free_space,
                        active_torrents=stats.active_torrents,
                        total_torrents=stats.total_torrents,
                        seeding_torrents=stats.seeding_torrents,
                        downloading_torrents=stats.downloading_torrents,
                        total_uploaded=stats.total_uploaded,
                        total_downloaded=stats.total_downloaded,
                    )
            finally:
                await client.disconnect()
        except asyncio.TimeoutError:
            logger.warning(f"下载器 {downloader.name} 连接超时")
        except ConnectionError as e:
            logger.warning(f"下载器 {downloader.name} 连接失败: {e}")
        except Exception as e:
            logger.error(f"获取下载器 {downloader.name} 状态异常: {e}")
        return DownloaderStatus(
            id=downloader.id,
            name=downloader.name,
            online=False,
        )

    # Fetch all statuses in parallel
    statuses = await asyncio.gather(
        *[get_single_status(dl) for dl in downloaders]
    )
    return list(statuses)


@router.post("", response_model=DownloaderResponse)
async def create_downloader_config(
    data: DownloaderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new downloader configuration"""
    downloader = Downloader(**data.model_dump())
    db.add(downloader)
    await db.commit()
    await db.refresh(downloader)
    return downloader


@router.get("/{downloader_id}", response_model=DownloaderResponse)
async def get_downloader(
    downloader_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific downloader"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")
    return downloader


@router.put("/{downloader_id}", response_model=DownloaderResponse)
async def update_downloader(
    downloader_id: int,
    data: DownloaderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a downloader configuration"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(downloader, key, value)

    await db.commit()
    await db.refresh(downloader)
    return downloader


@router.delete("/{downloader_id}")
async def delete_downloader(
    downloader_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a downloader"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    await db.delete(downloader)
    await db.commit()
    return {"message": "Downloader deleted"}


@router.post("/{downloader_id}/test")
async def test_downloader(
    downloader_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test downloader connection"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            success = await client.connect()
            if success:
                stats = await client.get_stats()
                return {
                    "success": True,
                    "message": "Connection successful",
                    "stats": {
                        "upload_speed": stats.upload_speed,
                        "download_speed": stats.download_speed,
                        "total_torrents": stats.total_torrents,
                        "free_space": stats.free_space,
                    }
                }
            else:
                return {"success": False, "message": "Connection failed"}
        finally:
            await client.disconnect()
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.get("/{downloader_id}/status", response_model=DownloaderStatus)
async def get_downloader_status(
    downloader_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get downloader status"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            if await client.connect():
                stats = await client.get_stats()
                return DownloaderStatus(
                    id=downloader.id,
                    name=downloader.name,
                    online=True,
                    upload_speed=stats.upload_speed,
                    download_speed=stats.download_speed,
                    free_space=stats.free_space,
                    active_torrents=stats.active_torrents,
                    total_torrents=stats.total_torrents,
                    seeding_torrents=stats.seeding_torrents,
                    downloading_torrents=stats.downloading_torrents,
                    total_uploaded=stats.total_uploaded,
                    total_downloaded=stats.total_downloaded,
                )
        finally:
            await client.disconnect()
    except asyncio.TimeoutError:
        logger.warning(f"下载器 {downloader.name} 状态获取超时")
    except Exception as e:
        logger.warning(f"获取下载器 {downloader.name} 状态失败: {e}")

    return DownloaderStatus(
        id=downloader.id,
        name=downloader.name,
        online=False,
    )


@router.get("/{downloader_id}/torrents", response_model=List[TorrentInfo])
async def get_downloader_torrents(
    downloader_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all torrents from a downloader"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            if await client.connect():
                torrents = await client.get_torrents()
                return [
                    TorrentInfo(
                        hash=t.hash,
                        name=t.name,
                        size=t.size,
                        progress=t.progress,
                        status=t.status,
                        uploaded=t.uploaded,
                        downloaded=t.downloaded,
                        ratio=t.ratio,
                        upload_speed=t.upload_speed,
                        download_speed=t.download_speed,
                        seeders=t.seeders,
                        leechers=t.leechers,
                        seeds_connected=t.seeds_connected,
                        peers_connected=t.peers_connected,
                        tracker=t.tracker,
                        tags=",".join(t.tags),
                        category=t.category,
                        save_path=t.save_path,
                        added_time=t.added_time,
                        seeding_time=t.seeding_time,
                        total_size=t.total_size,
                        selected_size=t.selected_size,
                        completed=t.completed,
                        completed_time=t.completed_time,
                        state=t.state,
                        tracker_status=t.tracker_status,
                    )
                    for t in torrents
                ]
        finally:
            await client.disconnect()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return []


@router.post("/{downloader_id}/torrents/{torrent_hash}/pause")
async def pause_torrent(
    downloader_id: int,
    torrent_hash: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause a torrent"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            if await client.connect():
                success = await client.pause_torrent(torrent_hash)
                if success:
                    return {"message": "Torrent paused"}
                raise HTTPException(status_code=500, detail="Failed to pause torrent")
        finally:
            await client.disconnect()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{downloader_id}/torrents/{torrent_hash}/resume")
async def resume_torrent(
    downloader_id: int,
    torrent_hash: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume a torrent"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            if await client.connect():
                success = await client.resume_torrent(torrent_hash)
                if success:
                    return {"message": "Torrent resumed"}
                raise HTTPException(status_code=500, detail="Failed to resume torrent")
        finally:
            await client.disconnect()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{downloader_id}/torrents/{torrent_hash}")
async def delete_torrent(
    downloader_id: int,
    torrent_hash: str,
    delete_files: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a torrent"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            if await client.connect():
                success = await client.remove_torrent(torrent_hash, delete_files)
                if success:
                    return {"message": "Torrent deleted"}
                raise HTTPException(status_code=500, detail="Failed to delete torrent")
        finally:
            await client.disconnect()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{downloader_id}/torrents/{torrent_hash}/reannounce")
async def reannounce_torrent(
    downloader_id: int,
    torrent_hash: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Force reannounce a torrent"""
    result = await db.execute(
        select(Downloader).where(Downloader.id == downloader_id)
    )
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    try:
        client = create_downloader(downloader)
        try:
            if await client.connect():
                success = await client.reannounce_torrent(torrent_hash)
                if success:
                    return {"message": "Torrent reannounced"}
                raise HTTPException(status_code=500, detail="Failed to reannounce torrent")
        finally:
            await client.disconnect()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
