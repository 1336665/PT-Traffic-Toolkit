"""Settings API endpoints for PT Manager"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, SystemSettings
from pydantic import BaseModel
from typing import Optional
from app.schemas import (
    TelegramSettings, TelegramSettingsUpdate, TelegramTestResult,
    NotificationSettings
)


class SiteSettings(BaseModel):
    site_name: str = "PT Manager"
    site_description: str = "PT 流量管理工具"


class SiteSettingsUpdate(BaseModel):
    site_name: Optional[str] = None
    site_description: Optional[str] = None
from app.services.auth import get_current_user
from app.services.notification import TelegramNotifier, init_notifier

router = APIRouter(prefix="/settings", tags=["Settings"])


async def _get_setting(db: AsyncSession, key: str) -> str:
    """Get a system setting value"""
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else ""


async def _set_setting(db: AsyncSession, key: str, value: str, commit: bool = True):
    """Set a system setting value"""
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = value
    else:
        setting = SystemSettings(key=key, value=value)
        db.add(setting)

    if commit:
        await db.commit()


@router.get("/telegram", response_model=TelegramSettings)
async def get_telegram_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get Telegram notification settings"""
    bot_token = await _get_setting(db, "telegram_bot_token")
    chat_id = await _get_setting(db, "telegram_chat_id")
    enabled = await _get_setting(db, "telegram_enabled")

    return TelegramSettings(
        bot_token=bot_token,
        chat_id=chat_id,
        enabled=enabled.lower() == "true" if enabled else False
    )


@router.put("/telegram", response_model=TelegramSettings)
async def update_telegram_settings(
    settings: TelegramSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update Telegram notification settings"""
    changed = False
    if settings.bot_token is not None:
        await _set_setting(db, "telegram_bot_token", settings.bot_token, commit=False)
        changed = True
    if settings.chat_id is not None:
        await _set_setting(db, "telegram_chat_id", settings.chat_id, commit=False)
        changed = True
    if settings.enabled is not None:
        await _set_setting(db, "telegram_enabled", str(settings.enabled).lower(), commit=False)
        changed = True

    if changed:
        await db.commit()

    # Reinitialize notifier with new settings
    bot_token = await _get_setting(db, "telegram_bot_token")
    chat_id = await _get_setting(db, "telegram_chat_id")
    init_notifier(bot_token, chat_id)

    enabled = await _get_setting(db, "telegram_enabled")

    return TelegramSettings(
        bot_token=bot_token,
        chat_id=chat_id,
        enabled=enabled.lower() == "true" if enabled else False
    )


@router.post("/telegram/test", response_model=TelegramTestResult)
async def test_telegram(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test Telegram connection and send a test message"""
    bot_token = await _get_setting(db, "telegram_bot_token")
    chat_id = await _get_setting(db, "telegram_chat_id")

    if not bot_token or not chat_id:
        return TelegramTestResult(
            success=False,
            message="Telegram not configured. Please set bot_token and chat_id first."
        )

    notifier = TelegramNotifier(bot_token, chat_id)
    success, message = await notifier.test_connection()

    return TelegramTestResult(success=success, message=message)


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notification settings"""
    bot_token = await _get_setting(db, "telegram_bot_token")
    chat_id = await _get_setting(db, "telegram_chat_id")
    enabled = await _get_setting(db, "telegram_enabled")

    telegram = TelegramSettings(
        bot_token=bot_token,
        chat_id=chat_id,
        enabled=enabled.lower() == "true" if enabled else False
    )

    notify_rss = await _get_setting(db, "notify_rss_download")
    notify_delete = await _get_setting(db, "notify_delete")
    notify_speed = await _get_setting(db, "notify_speed_limit")
    notify_error = await _get_setting(db, "notify_error")
    notify_disk = await _get_setting(db, "notify_low_disk")

    return NotificationSettings(
        telegram=telegram,
        notify_rss_download=notify_rss.lower() != "false" if notify_rss else True,
        notify_delete=notify_delete.lower() != "false" if notify_delete else True,
        notify_speed_limit=notify_speed.lower() != "false" if notify_speed else True,
        notify_error=notify_error.lower() != "false" if notify_error else True,
        notify_low_disk=notify_disk.lower() != "false" if notify_disk else True,
    )


@router.put("/notifications", response_model=NotificationSettings)
async def update_notification_settings(
    settings: NotificationSettings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update all notification settings"""
    # Update Telegram settings
    await _set_setting(db, "telegram_bot_token", settings.telegram.bot_token, commit=False)
    await _set_setting(db, "telegram_chat_id", settings.telegram.chat_id, commit=False)
    await _set_setting(db, "telegram_enabled", str(settings.telegram.enabled).lower(), commit=False)

    # Update notification toggles
    await _set_setting(db, "notify_rss_download", str(settings.notify_rss_download).lower(), commit=False)
    await _set_setting(db, "notify_delete", str(settings.notify_delete).lower(), commit=False)
    await _set_setting(db, "notify_speed_limit", str(settings.notify_speed_limit).lower(), commit=False)
    await _set_setting(db, "notify_error", str(settings.notify_error).lower(), commit=False)
    await _set_setting(db, "notify_low_disk", str(settings.notify_low_disk).lower(), commit=False)

    await db.commit()

    # Reinitialize notifier
    init_notifier(settings.telegram.bot_token, settings.telegram.chat_id)

    return settings


@router.get("/site", response_model=SiteSettings)
async def get_site_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get site customization settings"""
    site_name = await _get_setting(db, "site_name")
    site_description = await _get_setting(db, "site_description")

    return SiteSettings(
        site_name=site_name if site_name else "PT Manager",
        site_description=site_description if site_description else "PT 流量管理工具"
    )


@router.put("/site", response_model=SiteSettings)
async def update_site_settings(
    settings: SiteSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update site customization settings"""
    if settings.site_name is not None:
        await _set_setting(db, "site_name", settings.site_name, commit=False)
    if settings.site_description is not None:
        await _set_setting(db, "site_description", settings.site_description, commit=False)

    await db.commit()

    site_name = await _get_setting(db, "site_name")
    site_description = await _get_setting(db, "site_description")

    return SiteSettings(
        site_name=site_name if site_name else "PT Manager",
        site_description=site_description if site_description else "PT 流量管理工具"
    )


@router.get("/site/public")
async def get_site_settings_public(db: AsyncSession = Depends(get_db)):
    """Get site settings (no auth required, for login page)"""
    site_name = await _get_setting(db, "site_name")
    site_description = await _get_setting(db, "site_description")

    return {
        "site_name": site_name if site_name else "PT Manager",
        "site_description": site_description if site_description else "PT 流量管理工具"
    }
