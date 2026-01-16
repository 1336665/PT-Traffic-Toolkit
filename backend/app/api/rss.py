from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, RssFeed, RssRecord
from app.schemas import (
    RssFeedCreate,
    RssFeedUpdate,
    RssFeedResponse,
    RssRecordResponse,
)
from app.services.auth import get_current_user
from app.services.rss_service import RssService

router = APIRouter(prefix="/rss", tags=["RSS"])


@router.get("/feeds", response_model=List[RssFeedResponse])
async def get_feeds(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all RSS feeds"""
    result = await db.execute(select(RssFeed).order_by(RssFeed.id))
    return result.scalars().all()


@router.post("/feeds", response_model=RssFeedResponse)
async def create_feed(
    data: RssFeedCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new RSS feed"""
    feed = RssFeed(**data.model_dump())
    db.add(feed)
    await db.commit()
    await db.refresh(feed)
    return feed


@router.get("/feeds/{feed_id}", response_model=RssFeedResponse)
async def get_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific RSS feed"""
    result = await db.execute(select(RssFeed).where(RssFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    return feed


@router.put("/feeds/{feed_id}", response_model=RssFeedResponse)
async def update_feed(
    feed_id: int,
    data: RssFeedUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an RSS feed"""
    result = await db.execute(select(RssFeed).where(RssFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feed, key, value)

    await db.commit()
    await db.refresh(feed)
    return feed


@router.delete("/feeds/{feed_id}")
async def delete_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an RSS feed"""
    result = await db.execute(select(RssFeed).where(RssFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    await db.delete(feed)
    await db.commit()
    return {"message": "Feed deleted"}


@router.post("/feeds/{feed_id}/fetch")
async def fetch_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually fetch an RSS feed"""
    result = await db.execute(select(RssFeed).where(RssFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    service = RssService(db)
    try:
        records = await service.process_feed(feed)
        downloaded = [r for r in records if r.downloaded]
        return {
            "message": f"Feed fetched successfully",
            "total": len(records),
            "downloaded": len(downloaded),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feeds/{feed_id}/reset")
async def reset_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset feed first run status"""
    result = await db.execute(select(RssFeed).where(RssFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    feed.first_run_done = False
    feed.last_fetch = None
    await db.commit()
    return {"message": "Feed reset"}


@router.get("/records", response_model=List[RssRecordResponse])
async def get_records(
    feed_id: int = None,
    downloaded: bool = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RSS records"""
    query = select(RssRecord).order_by(desc(RssRecord.created_at))

    if feed_id is not None:
        query = query.where(RssRecord.feed_id == feed_id)
    if downloaded is not None:
        query = query.where(RssRecord.downloaded == downloaded)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/records/{record_id}", response_model=RssRecordResponse)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific RSS record"""
    result = await db.execute(select(RssRecord).where(RssRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an RSS record"""
    result = await db.execute(select(RssRecord).where(RssRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    await db.delete(record)
    await db.commit()
    return {"message": "Record deleted"}
