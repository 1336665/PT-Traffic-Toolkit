"""Context manager for downloader connections to prevent resource leaks"""

from contextlib import asynccontextmanager
from typing import Optional

from app.models import Downloader
from app.services.downloader import create_downloader
from app.services.downloader.base import BaseDownloader


@asynccontextmanager
async def downloader_client(downloader: Downloader):
    """
    Async context manager for safe downloader connections.

    Usage:
        async with downloader_client(downloader) as client:
            if client:
                stats = await client.get_stats()

    Always disconnects even if an exception occurs.
    Yields None if connection fails.
    """
    client: Optional[BaseDownloader] = None
    connected = False
    try:
        client = create_downloader(downloader)
        connected = await client.connect()
        if connected:
            yield client
        else:
            yield None
    finally:
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
