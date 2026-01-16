from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, U2MagicConfig, U2MagicRecord
from app.schemas import (
    U2MagicConfigUpdate,
    U2MagicConfigResponse,
    U2MagicRecordResponse,
)
from app.services.auth import get_current_user
from app.services.u2_magic import U2MagicService

router = APIRouter(prefix="/u2-magic", tags=["U2 Magic"])


@router.get("/config", response_model=U2MagicConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get U2 magic configuration"""
    result = await db.execute(select(U2MagicConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        # Create default config
        config = U2MagicConfig()
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


@router.put("/config", response_model=U2MagicConfigResponse)
async def update_config(
    data: U2MagicConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update U2 magic configuration"""
    result = await db.execute(select(U2MagicConfig).limit(1))
    config = result.scalar_one_or_none()

    if not config:
        config = U2MagicConfig()
        db.add(config)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.post("/fetch")
async def fetch_magic(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually fetch and process U2 magic"""
    service = U2MagicService(db)
    try:
        records = await service.process_magic()
        downloaded = [r for r in records if r.downloaded]
        return {
            "message": "Magic fetched",
            "total": len(records),
            "downloaded": len(downloaded),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records", response_model=List[U2MagicRecordResponse])
async def get_records(
    downloaded: bool = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get U2 magic records"""
    query = select(U2MagicRecord).order_by(desc(U2MagicRecord.created_at))

    if downloaded is not None:
        query = query.where(U2MagicRecord.downloaded == downloaded)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/records/{record_id}", response_model=U2MagicRecordResponse)
async def get_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific U2 magic record"""
    result = await db.execute(select(U2MagicRecord).where(U2MagicRecord.id == record_id))
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
    """Delete a U2 magic record"""
    result = await db.execute(select(U2MagicRecord).where(U2MagicRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    await db.delete(record)
    await db.commit()
    return {"message": "Record deleted"}
