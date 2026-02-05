from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, TrafficBudgetConfig
from app.schemas import TrafficBudgetConfigResponse, TrafficBudgetConfigUpdate, TrafficBudgetStatus
from app.services.auth import get_current_user
from app.services.traffic_budget import TrafficBudgetService


router = APIRouter(prefix="/traffic-budget", tags=["Traffic Budget"])


@router.get("/config", response_model=TrafficBudgetConfigResponse)
async def get_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TrafficBudgetService(db)
    return await service.get_or_create_config()


@router.put("/config", response_model=TrafficBudgetConfigResponse)
async def update_config(
    data: TrafficBudgetConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(TrafficBudgetConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = TrafficBudgetConfig()
        db.add(config)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.get("/status", response_model=TrafficBudgetStatus)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TrafficBudgetService(db)
    status = await service.get_status()
    return TrafficBudgetStatus(**status)
