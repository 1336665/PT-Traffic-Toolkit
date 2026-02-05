"""Telegram notification service for PT Manager"""

import asyncio
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
import httpx

from app.config import settings
from app.database import async_session_maker
from app.models import WebhookEndpoint
from app.services.webhooks import deliver_webhook
from app.utils import get_logger

logger = get_logger('pt_manager.notification')


async def _notify_webhooks(event: str, payload: dict) -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(WebhookEndpoint).where(WebhookEndpoint.enabled == True)
        )
        for webhook in result.scalars().all():
            await deliver_webhook(webhook, event, payload)


class TelegramNotifier:
    """Telegram notification service with rate limiting and batching"""

    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self._message_queue: List[str] = []
        self._last_send_time: Optional[datetime] = None
        self._min_interval = 1.0  # Minimum seconds between messages

    @property
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)

    async def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> bool:
        """Send a message to Telegram

        Args:
            text: Message text (HTML or plain text)
            parse_mode: "HTML" or "Markdown" or "" for plain text
            disable_notification: If True, send silently

        Returns:
            True if message was sent successfully
        """
        if not self.is_configured:
            logger.debug("Telegram not configured, skipping notification")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_notification": disable_notification
        }

        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            # Rate limiting
            if self._last_send_time:
                elapsed = (datetime.utcnow() - self._last_send_time).total_seconds()
                if elapsed < self._min_interval:
                    await asyncio.sleep(self._min_interval - elapsed)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                if result.get("ok"):
                    self._last_send_time = datetime.utcnow()
                    logger.debug(f"Telegram message sent successfully")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description', 'Unknown error')}")
                    return False

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limited, wait and retry
                retry_after = int(e.response.headers.get("Retry-After", 5))
                logger.warning(f"Telegram rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self.send_message(text, parse_mode, disable_notification)
            logger.error(f"Telegram HTTP error: {e.response.status_code}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def test_connection(self) -> tuple[bool, str]:
        """Test Telegram connection and return status message"""
        if not self.is_configured:
            return False, "Telegram not configured (missing bot_token or chat_id)"

        try:
            # Test bot token by getting bot info
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                result = response.json()

                if not result.get("ok"):
                    return False, f"Invalid bot token: {result.get('description', 'Unknown error')}"

                bot_name = result.get("result", {}).get("username", "Unknown")

            # Try sending a test message
            success = await self.send_message(
                f"PT Manager test notification\nBot: @{bot_name}\nTime: {datetime.utcnow().isoformat()}"
            )

            if success:
                return True, f"Connected to bot @{bot_name}"
            else:
                return False, "Failed to send test message (check chat_id)"

        except Exception as e:
            return False, f"Connection error: {str(e)}"


# Notification message templates
class NotificationTemplates:
    """Pre-defined notification message templates"""

    @staticmethod
    def rss_download(feed_name: str, torrent_name: str, size_gb: float) -> str:
        """RSS torrent downloaded notification"""
        return (
            f"<b>RSS Download</b>\n"
            f"Feed: {_escape_html(feed_name)}\n"
            f"Torrent: {_escape_html(torrent_name[:100])}\n"
            f"Size: {size_gb:.2f} GB"
        )

    @staticmethod
    def rss_batch_download(feed_name: str, count: int, total_size_gb: float) -> str:
        """RSS batch download notification"""
        return (
            f"<b>RSS Batch Download</b>\n"
            f"Feed: {_escape_html(feed_name)}\n"
            f"Downloaded: {count} torrents\n"
            f"Total size: {total_size_gb:.2f} GB"
        )

    @staticmethod
    def delete_action(rule_name: str, torrent_name: str, ratio: float, seeding_hours: float) -> str:
        """Torrent deleted notification"""
        return (
            f"<b>Torrent Deleted</b>\n"
            f"Rule: {_escape_html(rule_name)}\n"
            f"Torrent: {_escape_html(torrent_name[:100])}\n"
            f"Ratio: {ratio:.2f}\n"
            f"Seeding: {seeding_hours:.1f}h"
        )

    @staticmethod
    def delete_batch(rule_name: str, count: int, total_uploaded_gb: float) -> str:
        """Batch delete notification"""
        return (
            f"<b>Batch Delete</b>\n"
            f"Rule: {_escape_html(rule_name)}\n"
            f"Deleted: {count} torrents\n"
            f"Total uploaded: {total_uploaded_gb:.2f} GB"
        )

    @staticmethod
    def speed_limit_report(
        tracker: str,
        current_speed_mbps: float,
        target_speed_mbps: float,
        uploaded_gb: float,
        phase: str
    ) -> str:
        """Speed limit status report"""
        return (
            f"<b>Speed Limit Report</b>\n"
            f"Tracker: {_escape_html(tracker)}\n"
            f"Speed: {current_speed_mbps:.2f} MB/s (target: {target_speed_mbps:.2f})\n"
            f"Uploaded: {uploaded_gb:.2f} GB\n"
            f"Phase: {phase}"
        )

    @staticmethod
    def speed_limit_complete(tracker: str, total_uploaded_gb: float, duration_hours: float) -> str:
        """Speed limit target reached notification"""
        return (
            f"<b>Speed Limit Complete</b>\n"
            f"Tracker: {_escape_html(tracker)}\n"
            f"Total uploaded: {total_uploaded_gb:.2f} GB\n"
            f"Duration: {duration_hours:.1f}h"
        )

    @staticmethod
    def u2_magic_download(torrent_name: str, magic_type: str, size_gb: float) -> str:
        """U2 magic torrent downloaded notification"""
        return (
            f"<b>U2 Magic Download</b>\n"
            f"Torrent: {_escape_html(torrent_name[:100])}\n"
            f"Magic: {_escape_html(magic_type)}\n"
            f"Size: {size_gb:.2f} GB"
        )

    @staticmethod
    def error_alert(module: str, error_message: str) -> str:
        """Error alert notification"""
        return (
            f"<b>Error Alert</b>\n"
            f"Module: {_escape_html(module)}\n"
            f"Error: {_escape_html(error_message[:500])}"
        )

    @staticmethod
    def downloader_offline(downloader_name: str) -> str:
        """Downloader went offline notification"""
        return (
            f"<b>Downloader Offline</b>\n"
            f"Name: {_escape_html(downloader_name)}\n"
            f"Status: Connection failed"
        )

    @staticmethod
    def low_disk_space(downloader_name: str, free_space_gb: float, threshold_gb: float) -> str:
        """Low disk space warning"""
        return (
            f"<b>Low Disk Space Warning</b>\n"
            f"Downloader: {_escape_html(downloader_name)}\n"
            f"Free: {free_space_gb:.2f} GB\n"
            f"Threshold: {threshold_gb:.2f} GB"
        )


def _escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# Global notifier instance
_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """Get global Telegram notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


def init_notifier(bot_token: str = "", chat_id: str = ""):
    """Initialize or reinitialize the global notifier"""
    global _notifier
    _notifier = TelegramNotifier(bot_token, chat_id)
    return _notifier


# Convenience functions for sending notifications
async def notify_rss_download(feed_name: str, torrent_name: str, size_bytes: float) -> bool:
    """Send RSS download notification"""
    notifier = get_notifier()
    size_gb = size_bytes / (1024 ** 3)
    message = NotificationTemplates.rss_download(feed_name, torrent_name, size_gb)
    await _notify_webhooks("rss_download", {
        "feed_name": feed_name,
        "torrent_name": torrent_name,
        "size_bytes": size_bytes,
    })
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_rss_batch(feed_name: str, count: int, total_size_bytes: float) -> bool:
    """Send RSS batch download notification"""
    notifier = get_notifier()
    total_gb = total_size_bytes / (1024 ** 3)
    message = NotificationTemplates.rss_batch_download(feed_name, count, total_gb)
    await _notify_webhooks("rss_batch", {
        "feed_name": feed_name,
        "count": count,
        "total_size_bytes": total_size_bytes,
    })
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_delete(rule_name: str, torrent_name: str, ratio: float, seeding_seconds: int) -> bool:
    """Send delete notification"""
    notifier = get_notifier()
    seeding_hours = seeding_seconds / 3600
    message = NotificationTemplates.delete_action(rule_name, torrent_name, ratio, seeding_hours)
    await _notify_webhooks("delete", {
        "rule_name": rule_name,
        "torrent_name": torrent_name,
        "ratio": ratio,
        "seeding_seconds": seeding_seconds,
    })
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_delete_batch(rule_name: str, count: int, total_uploaded_bytes: float) -> bool:
    """Send batch delete notification"""
    notifier = get_notifier()
    total_gb = total_uploaded_bytes / (1024 ** 3)
    message = NotificationTemplates.delete_batch(rule_name, count, total_gb)
    await _notify_webhooks("delete_batch", {
        "rule_name": rule_name,
        "count": count,
        "total_uploaded_bytes": total_uploaded_bytes,
    })
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_speed_limit(
    tracker: str,
    current_speed: float,
    target_speed: float,
    uploaded: float,
    phase: str
) -> bool:
    """Send speed limit report notification"""
    notifier = get_notifier()
    current_mbps = current_speed / (1024 ** 2)
    target_mbps = target_speed / (1024 ** 2)
    uploaded_gb = uploaded / (1024 ** 3)
    message = NotificationTemplates.speed_limit_report(tracker, current_mbps, target_mbps, uploaded_gb, phase)
    await _notify_webhooks("speed_limit", {
        "tracker": tracker,
        "current_speed": current_speed,
        "target_speed": target_speed,
        "uploaded": uploaded,
        "phase": phase,
    })
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_error(module: str, error_message: str) -> bool:
    """Send error alert notification"""
    notifier = get_notifier()
    message = NotificationTemplates.error_alert(module, error_message)
    await _notify_webhooks("error", {"module": module, "error_message": error_message})
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_downloader_offline(downloader_name: str) -> bool:
    """Send downloader offline notification"""
    notifier = get_notifier()
    message = NotificationTemplates.downloader_offline(downloader_name)
    await _notify_webhooks("downloader_offline", {"downloader_name": downloader_name})
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)


async def notify_low_disk_space(downloader_name: str, free_space_bytes: float, threshold_bytes: float) -> bool:
    """Send low disk space warning"""
    notifier = get_notifier()
    free_gb = free_space_bytes / (1024 ** 3)
    threshold_gb = threshold_bytes / (1024 ** 3)
    message = NotificationTemplates.low_disk_space(downloader_name, free_gb, threshold_gb)
    await _notify_webhooks("low_disk_space", {
        "downloader_name": downloader_name,
        "free_space_bytes": free_space_bytes,
        "threshold_bytes": threshold_bytes,
    })
    if not notifier.is_configured:
        return False
    return await notifier.send_message(message)
