from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Downloader
from app.schemas import TorrentScore, LifecycleActionRequest
from app.services.auth import get_current_user
from app.services.downloader.context import downloader_client
from app.services.lifecycle import score_torrents


router = APIRouter(prefix="/lifecycle", tags=["Lifecycle"])


@router.get("/scores", response_model=list[TorrentScore])
async def get_scores(
    downloader_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Downloader).where(Downloader.id == downloader_id))
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    async with downloader_client(downloader) as client:
        if not client:
            raise HTTPException(status_code=400, detail="Downloader unavailable")
        torrents = await client.get_torrents()

    return score_torrents(torrents)


@router.post("/actions")
async def apply_lifecycle_action(
    data: LifecycleActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Downloader).where(Downloader.id == data.downloader_id))
    downloader = result.scalar_one_or_none()
    if not downloader:
        raise HTTPException(status_code=404, detail="Downloader not found")

    action = data.action.lower()
    results = []
    async with downloader_client(downloader) as client:
        if not client:
            raise HTTPException(status_code=400, detail="Downloader unavailable")
        for torrent_hash in data.torrent_hashes:
            if action == "pause":
                ok = await client.pause_torrent(torrent_hash)
            elif action == "resume":
                ok = await client.resume_torrent(torrent_hash)
            elif action == "archive":
                ok = True
                if data.archive_path:
                    ok = await client.set_torrent_location(torrent_hash, data.archive_path)
                tag_ok = await client.add_torrent_tags(torrent_hash, ["archived"])
                ok = ok and tag_ok
            else:
                raise HTTPException(status_code=400, detail="Unsupported action")
            results.append({"hash": torrent_hash, "success": ok})

    return {"results": results}
