from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.models import WebhookEndpoint
from app.utils import get_logger

logger = get_logger("pt_manager.webhooks")


async def deliver_webhook(webhook: WebhookEndpoint, event: str, payload: dict[str, Any]) -> tuple[bool, str]:
    if not webhook.enabled:
        return False, "Webhook disabled"

    if webhook.events and event not in webhook.events:
        return False, "Event filtered"

    headers = {"Content-Type": "application/json"}
    if webhook.secret:
        headers["X-Webhook-Secret"] = webhook.secret

    data = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(webhook.url, json=data, headers=headers)
            response.raise_for_status()
        return True, "Delivered"
    except Exception as exc:
        logger.warning("Webhook delivery failed for %s: %s", webhook.url, exc)
        return False, str(exc)


async def test_webhook_delivery(webhook: WebhookEndpoint) -> tuple[bool, str]:
    payload = {"message": "PT Manager webhook test"}
    return await deliver_webhook(webhook, "test", payload)
