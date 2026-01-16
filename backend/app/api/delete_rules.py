from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, DeleteRule, DeleteRecord
from app.schemas import (
    DeleteRuleCreate,
    DeleteRuleUpdate,
    DeleteRuleResponse,
    DeleteRecordResponse,
)
from app.services.auth import get_current_user
from app.services.delete_service import DeleteService

router = APIRouter(prefix="/delete-rules", tags=["Delete Rules"])


@router.get("", response_model=List[DeleteRuleResponse])
async def get_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all delete rules"""
    result = await db.execute(
        select(DeleteRule).order_by(desc(DeleteRule.priority), DeleteRule.id)
    )
    return result.scalars().all()


@router.post("", response_model=DeleteRuleResponse)
async def create_rule(
    data: DeleteRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new delete rule"""
    # Convert conditions to JSON serializable format
    rule_data = data.model_dump()
    rule_data['conditions'] = [c.model_dump() for c in data.conditions]

    rule = DeleteRule(**rule_data)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=DeleteRuleResponse)
async def get_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific delete rule"""
    result = await db.execute(select(DeleteRule).where(DeleteRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.put("/{rule_id}", response_model=DeleteRuleResponse)
async def update_rule(
    rule_id: int,
    data: DeleteRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a delete rule"""
    result = await db.execute(select(DeleteRule).where(DeleteRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = data.model_dump(exclude_unset=True)

    # Convert conditions if provided
    if 'conditions' in update_data and update_data['conditions'] is not None:
        update_data['conditions'] = [c.model_dump() for c in data.conditions]

    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a delete rule"""
    result = await db.execute(select(DeleteRule).where(DeleteRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()
    return {"message": "Rule deleted"}


@router.post("/{rule_id}/run")
async def run_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually run a delete rule"""
    result = await db.execute(select(DeleteRule).where(DeleteRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    service = DeleteService(db)
    try:
        deleted = await service.execute_rule(rule)
        return {
            "message": f"Rule executed",
            "deleted_count": len(deleted),
            "deleted": [
                {
                    "name": r.torrent_name,
                    "size": r.size,
                    "ratio": r.ratio,
                }
                for r in deleted
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rule_id}/preview")
async def preview_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview which torrents would be deleted by a rule"""
    result = await db.execute(select(DeleteRule).where(DeleteRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    from app.models import Downloader
    service = DeleteService(db)

    # Get applicable downloaders
    if rule.downloader_ids:
        dl_result = await db.execute(
            select(Downloader).where(Downloader.id.in_(rule.downloader_ids))
        )
    else:
        dl_result = await db.execute(select(Downloader).where(Downloader.enabled == True))

    downloaders = dl_result.scalars().all()
    matches = []

    for downloader in downloaders:
        try:
            matching = await service.get_matching_torrents(rule, downloader)
            for torrent, duration_met in matching:
                matches.append({
                    "downloader": downloader.name,
                    "name": torrent.name,
                    "hash": torrent.hash,
                    "size": torrent.size,
                    "ratio": torrent.ratio,
                    "seeding_time": torrent.seeding_time,
                    "duration_met": duration_met,
                })
        except Exception as e:
            print(f"Error previewing rule for {downloader.name}: {e}")

    return {"matches": matches, "total": len(matches)}


@router.get("/records/all", response_model=List[DeleteRecordResponse])
async def get_delete_records(
    rule_id: int = None,
    downloader_id: int = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get delete records"""
    query = select(DeleteRecord).order_by(desc(DeleteRecord.deleted_at))

    if rule_id is not None:
        query = query.where(DeleteRecord.rule_id == rule_id)
    if downloader_id is not None:
        query = query.where(DeleteRecord.downloader_id == downloader_id)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
