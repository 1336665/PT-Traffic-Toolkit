from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import TrafficBudgetConfig, SpeedLimitRecord
from app.utils.timezone import local_month_start_utc


class TrafficBudgetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_config(self) -> TrafficBudgetConfig:
        result = await self.db.execute(select(TrafficBudgetConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            config = TrafficBudgetConfig()
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
        return config

    def _get_period_range(self, config: TrafficBudgetConfig) -> tuple[datetime, datetime]:
        now = datetime.utcnow()
        period_start = local_month_start_utc(now)
        reset_day = max(1, min(28, int(config.reset_day or 1)))
        if reset_day != 1:
            local_start = local_month_start_utc(now).replace(day=reset_day)
            if now < local_start:
                last_month = (local_start.replace(day=1) - timedelta(days=1)).replace(day=reset_day)
                period_start = last_month
            else:
                period_start = local_start
        period_end = period_start + timedelta(days=32)
        period_end = period_end.replace(day=1)
        return period_start, period_end

    async def get_status(self) -> dict:
        config = await self.get_or_create_config()
        period_start, period_end = self._get_period_range(config)

        speed_result = await self.db.execute(
            select(
                func.coalesce(func.sum(SpeedLimitRecord.uploaded), 0),
                func.coalesce(func.sum(SpeedLimitRecord.downloaded), 0),
            ).where(
                SpeedLimitRecord.created_at >= period_start,
                SpeedLimitRecord.created_at < period_end,
            )
        )
        row = speed_result.first()
        uploaded = float(row[0] or 0)
        downloaded = float(row[1] or 0)
        total_gb = (uploaded + downloaded) / (1024 ** 3)
        quota_gb = float(config.monthly_quota_gb or 0)
        usage_ratio = total_gb / quota_gb if quota_gb > 0 else 0
        remaining_gb = max(0.0, quota_gb - total_gb)
        warning = quota_gb > 0 and usage_ratio >= float(config.warning_threshold or 0.8)
        exceeded = quota_gb > 0 and usage_ratio >= 1.0

        return {
            "period_start": period_start,
            "period_end": period_end,
            "uploaded_gb": uploaded / (1024 ** 3),
            "downloaded_gb": downloaded / (1024 ** 3),
            "total_gb": total_gb,
            "quota_gb": quota_gb,
            "usage_ratio": usage_ratio,
            "remaining_gb": remaining_gb,
            "warning": warning,
            "exceeded": exceeded,
        }
