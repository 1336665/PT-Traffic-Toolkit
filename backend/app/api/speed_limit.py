from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, SpeedLimitConfig, SpeedLimitSite, SpeedLimitRecord
from app.schemas import (
    SpeedLimitConfigUpdate,
    SpeedLimitConfigResponse,
    SpeedLimitSiteCreate,
    SpeedLimitSiteUpdate,
    SpeedLimitSiteResponse,
    SpeedLimitRecordResponse,
)
from app.services.auth import get_current_user
from app.services.speed_limiter import SpeedLimiterService

router = APIRouter(prefix="/speed-limit", tags=["Speed Limit"])


@router.get("/config", response_model=SpeedLimitConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get speed limit configuration"""
    result = await db.execute(select(SpeedLimitConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config
        config = SpeedLimitConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


@router.put("/config", response_model=SpeedLimitConfigResponse)
async def update_config(
    data: SpeedLimitConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update speed limit configuration"""
    result = await db.execute(select(SpeedLimitConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = SpeedLimitConfig()
        db.add(config)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.get("/sites", response_model=List[SpeedLimitSiteResponse])
async def get_sites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all site-specific speed limit rules"""
    result = await db.execute(select(SpeedLimitSite).order_by(SpeedLimitSite.id))
    return result.scalars().all()


@router.post("/sites", response_model=SpeedLimitSiteResponse)
async def create_site(
    data: SpeedLimitSiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a site-specific speed limit rule"""
    # Check for duplicate
    result = await db.execute(
        select(SpeedLimitSite).where(SpeedLimitSite.tracker_domain == data.tracker_domain)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Site already exists")

    site = SpeedLimitSite(**data.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


@router.get("/sites/{site_id}", response_model=SpeedLimitSiteResponse)
async def get_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific site rule"""
    result = await db.execute(select(SpeedLimitSite).where(SpeedLimitSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.put("/sites/{site_id}", response_model=SpeedLimitSiteResponse)
async def update_site(
    site_id: int,
    data: SpeedLimitSiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a site-specific rule"""
    result = await db.execute(select(SpeedLimitSite).where(SpeedLimitSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(site, key, value)

    await db.commit()
    await db.refresh(site)
    return site


@router.delete("/sites/{site_id}")
async def delete_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a site-specific rule"""
    result = await db.execute(select(SpeedLimitSite).where(SpeedLimitSite.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    await db.delete(site)
    await db.commit()
    return {"message": "Site deleted"}


@router.get("/status")
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current speed limiting status with caching for fast response"""
    service = SpeedLimiterService(db)
    await service.load_state()
    # 使用缓存机制获取状态（缓存3秒，过期则刷新）
    # refresh_status 会从下载器获取实时数据，不会显示已删除的种子
    return await service.get_cached_status()


@router.post("/apply")
async def apply_limits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually apply speed limits"""
    service = SpeedLimiterService(db)
    try:
        await service.load_state()  # 先加载已保存的状态
        results = await service.apply_limits()
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_limits(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all speed limits"""
    service = SpeedLimiterService(db)
    try:
        await service.clear_limits()
        return {"message": "Limits cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records", response_model=List[SpeedLimitRecordResponse])
async def get_records(
    tracker_domain: str = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get speed limit records"""
    query = select(SpeedLimitRecord).order_by(desc(SpeedLimitRecord.created_at))

    if tracker_domain:
        query = query.where(SpeedLimitRecord.tracker_domain == tracker_domain)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
