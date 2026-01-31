import traceback
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database import get_db
from app.models import User, RssFeed, RssRecord
from app.schemas import (
    RssFeedCreate,
    RssFeedUpdate,
    RssFeedResponse,
    RssRecordResponse,
    PaginatedResponse,
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


@router.get("/records")
async def get_records(
    feed_id: int = None,
    downloaded: bool = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RSS records with pagination"""
    # Build base query with filters
    base_query = select(RssRecord)
    if feed_id is not None:
        base_query = base_query.where(RssRecord.feed_id == feed_id)
    if downloaded is not None:
        base_query = base_query.where(RssRecord.downloaded == downloaded)

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Get paginated records
    offset = (page - 1) * page_size
    query = base_query.order_by(desc(RssRecord.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


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


@router.post("/feeds/{feed_id}/test")
async def test_feed(
    feed_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test RSS feed parsing without downloading - useful for debugging"""
    result = await db.execute(select(RssFeed).where(RssFeed.id == feed_id))
    feed = result.scalar_one_or_none()
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")

    service = RssService(db)

    # First, try to fetch the raw response to get more details
    test_info = {}
    try:
        from app.config import settings
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=settings.HTTP_VERIFY_SSL) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
            }
            response = await client.get(feed.url, headers=headers)
            test_info = {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "content_length": len(response.content),
                "is_cloudflare": "cf-ray" in str(response.headers).lower() or "cloudflare" in response.text[:1000].lower(),
            }
            if response.status_code != 200:
                test_info["response_preview"] = response.text[:500]
    except Exception as e:
        test_info = {"request_error": str(e)}

    try:
        entries = await service.fetch_feed(feed)

        # Extract info from entries
        parsed_entries = []
        for entry in entries[:10]:  # Limit to 10 for testing
            info = service.extract_torrent_info(entry, feed)
            passed, skip_reason = service.filter_torrent(info, feed)
            parsed_entries.append({
                "title": info["title"],
                "link": info["link"][:100] + "..." if len(info["link"]) > 100 else info["link"],
                "size": info["size"],
                "seeders": info["seeders"],
                "leechers": info["leechers"],
                "is_free": info["is_free"],
                "is_hr": info["is_hr"],
                "passed_filter": passed,
                "skip_reason": skip_reason or None,
            })

        return {
            "success": len(entries) > 0,
            "total_entries": len(entries),
            "first_run_done": feed.first_run_done,
            "message": "首次运行时只记录不下载，需要再次抓取才会下载" if not feed.first_run_done else None,
            "entries": parsed_entries,
            "request_info": test_info,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "request_info": test_info,
        }
