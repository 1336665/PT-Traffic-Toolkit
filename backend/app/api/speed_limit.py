from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, SpeedLimitConfig, SpeedLimitRecord
from app.schemas import SpeedLimitConfigResponse, SpeedLimitConfigUpdate, SpeedLimitRecordResponse
from app.services.auth import get_current_user
from app.services.speed_limiter import SpeedLimiterService

router = APIRouter(prefix="/speed-limit", tags=["Speed Limit"])


@router.get("/config", response_model=SpeedLimitConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SpeedLimiterService(db)
    return await service.ensure_config()


@router.put("/config", response_model=SpeedLimitConfigResponse)
async def update_config(
    data: SpeedLimitConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SpeedLimiterService(db)
    config = await service.ensure_config()
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    await db.commit()
    await db.refresh(config)
    return config


@router.get("/status")
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SpeedLimiterService(db)
    await service.load_state()
    return await service.get_cached_status()


@router.post("/apply")
async def apply_limits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SpeedLimiterService(db)
    await service.load_state()
    try:
        return await service.apply_limits()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/clear")
async def clear_limits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SpeedLimiterService(db)
    await service.load_state()
    try:
        await service.clear_limits()
        return {"message": "Limits cleared"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/records", response_model=List[SpeedLimitRecordResponse])
async def get_records(
    tracker_domain: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(SpeedLimitRecord).order_by(desc(SpeedLimitRecord.created_at))
    if tracker_domain:
        query = query.where(SpeedLimitRecord.tracker_domain == tracker_domain)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
