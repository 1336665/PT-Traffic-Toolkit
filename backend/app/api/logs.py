"""Logs API endpoints"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, delete, func

from app.database import get_db
from app.models.models import LogRecord, LogLevel
from app.api.auth import get_current_user
from pydantic import BaseModel


router = APIRouter(prefix="/logs", tags=["logs"])


class LogResponse(BaseModel):
    id: int
    timestamp: datetime
    level: str
    module: str
    message: str
    details: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[LogResponse])
async def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = None,
    module: Optional[str] = None,
    hours: Optional[int] = Query(None, ge=1, le=168),  # Max 7 days
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """Get system logs with optional filtering"""
    query = select(LogRecord)

    # Filter by level
    if level:
        try:
            level_enum = LogLevel(level)
            query = query.where(LogRecord.level == level_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid log level: {level}")

    # Filter by module
    if module:
        query = query.where(LogRecord.module == module)

    # Filter by time range
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.where(LogRecord.timestamp >= since)

    # Order by timestamp descending (newest first) and limit
    query = query.order_by(desc(LogRecord.timestamp)).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        LogResponse(
            id=log.id,
            timestamp=log.timestamp,
            level=log.level.value,
            module=log.module,
            message=log.message,
            details=log.details or ""
        )
        for log in logs
    ]


@router.delete("")
async def clear_logs(
    before_hours: int = Query(24, ge=1, description="Clear logs older than X hours"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """Clear old logs"""
    before = datetime.utcnow() - timedelta(hours=before_hours)
    stmt = delete(LogRecord).where(LogRecord.timestamp < before)
    result = await db.execute(stmt)
    await db.commit()
    deleted = result.rowcount

    return {"deleted": deleted, "message": f"Deleted {deleted} log records"}


@router.get("/stats")
async def get_log_stats(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    """Get log statistics"""
    since = datetime.utcnow() - timedelta(hours=hours)

    stats = {}
    for level in LogLevel:
        stmt = select(func.count()).select_from(LogRecord).where(
            LogRecord.level == level,
            LogRecord.timestamp >= since
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        stats[level.value] = count

    total = sum(stats.values())

    return {
        "total": total,
        "by_level": stats,
        "hours": hours
    }
