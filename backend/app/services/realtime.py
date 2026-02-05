from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket
from sqlalchemy import select

from app.database import async_session_maker
from app.models import Downloader, LogRecord
from app.services.downloader.context import downloader_client
from app.services.speed_limiter import SpeedLimiterService
from app.utils import get_logger
from app.api.dashboard import _fetch_downloader_stats, _fetch_downloader_status
from app.api.dashboard import get_services_status as services_status_handler

logger = get_logger("pt_manager.realtime")


class RealtimeConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    @property
    def has_connections(self) -> bool:
        return bool(self._connections)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        if not self._connections:
            return
        message = json.dumps(payload, default=str)
        stale = []
        for websocket in self._connections:
            try:
                await websocket.send_text(message)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


class RealtimeBroadcaster:
    def __init__(self, manager: RealtimeConnectionManager) -> None:
        self.manager = manager
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_log_id = 0
        self._last_torrent_state: dict[int, dict[str, str]] = {}

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        next_dashboard = 0.0
        next_services = 0.0
        next_speed_limit = 0.0
        next_logs = 0.0
        next_torrents = 0.0

        while self._running:
            if not self.manager.has_connections:
                await asyncio.sleep(1)
                continue

            now = asyncio.get_event_loop().time()
            try:
                async with async_session_maker() as db:
                    if now >= next_dashboard:
                        await self._broadcast_dashboard(db)
                        next_dashboard = now + 2.0

                    if now >= next_services:
                        await self._broadcast_services_status(db)
                        next_services = now + 5.0

                    if now >= next_speed_limit:
                        await self._broadcast_speed_limit(db)
                        next_speed_limit = now + 2.0

                    if now >= next_logs:
                        await self._broadcast_logs(db)
                        next_logs = now + 2.0

                    if now >= next_torrents:
                        await self._broadcast_torrents(db)
                        next_torrents = now + 5.0
            except Exception as exc:
                logger.warning("Realtime loop error: %s", exc)

            await asyncio.sleep(0.5)

    async def _broadcast_dashboard(self, db) -> None:
        result = await db.execute(select(Downloader).where(Downloader.enabled == True))
        downloaders = result.scalars().all()

        tasks = [
            asyncio.wait_for(_fetch_downloader_stats(dl), timeout=15.0)
            for dl in downloaders
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_upload_speed = 0
        total_download_speed = 0
        total_uploaded = 0
        total_downloaded = 0
        active_torrents = 0
        seeding_torrents = 0
        downloading_torrents = 0
        total_torrents = 0
        total_size = 0
        free_space = 0

        for res in results:
            if isinstance(res, dict):
                total_upload_speed += res["upload_speed"]
                total_download_speed += res["download_speed"]
                total_uploaded += res["total_uploaded"]
                total_downloaded += res["total_downloaded"]
                active_torrents += res["active_torrents"]
                seeding_torrents += res["seeding_torrents"]
                downloading_torrents += res["downloading_torrents"]
                total_torrents += res["total_torrents"]
                total_size += res["total_size"]
                free_space += res["free_space"]

        payload = {
            "type": "dashboard_stats",
            "payload": {
                "total_upload_speed": total_upload_speed,
                "total_download_speed": total_download_speed,
                "total_uploaded": total_uploaded,
                "total_downloaded": total_downloaded,
                "active_torrents": active_torrents,
                "seeding_torrents": seeding_torrents,
                "downloading_torrents": downloading_torrents,
                "total_torrents": total_torrents,
                "total_size": total_size,
                "free_space": free_space,
            },
        }
        await self.manager.broadcast(payload)

        tasks = [
            asyncio.wait_for(_fetch_downloader_status(dl), timeout=10.0)
            for dl in downloaders
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        statuses = []
        for idx, res in enumerate(results):
            if isinstance(res, dict):
                statuses.append(res)
            else:
                dl = downloaders[idx]
                statuses.append({
                    "id": dl.id,
                    "name": dl.name,
                    "type": dl.type.value,
                    "enabled": dl.enabled,
                    "online": False,
                    "upload_speed": 0,
                    "download_speed": 0,
                    "free_space": 0,
                    "total_torrents": 0,
                })

        await self.manager.broadcast({
            "type": "downloaders_status",
            "payload": statuses,
        })

    async def _broadcast_services_status(self, db) -> None:
        status = await services_status_handler(db=db, current_user=None)  # type: ignore[arg-type]
        await self.manager.broadcast({"type": "services_status", "payload": status})

    async def _broadcast_speed_limit(self, db) -> None:
        service = SpeedLimiterService(db)
        await service.load_state()
        status = await service.get_cached_status()
        await self.manager.broadcast({"type": "speed_limit_status", "payload": status})

    async def _broadcast_logs(self, db) -> None:
        result = await db.execute(
            select(LogRecord).where(LogRecord.id > self._last_log_id).order_by(LogRecord.id).limit(200)
        )
        logs = result.scalars().all()
        if not logs:
            return
        self._last_log_id = logs[-1].id
        payload = [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level.value if hasattr(log.level, "value") else str(log.level),
                "module": log.module or "system",
                "message": log.message or "",
                "details": log.details or "",
            }
            for log in logs
        ]
        await self.manager.broadcast({"type": "logs", "payload": payload})

    async def _broadcast_torrents(self, db) -> None:
        result = await db.execute(select(Downloader).where(Downloader.enabled == True))
        downloaders = result.scalars().all()

        for downloader in downloaders:
            try:
                async with downloader_client(downloader) as client:
                    if not client:
                        continue
                    torrents = await client.get_torrents()
            except Exception:
                continue

            current_state: dict[str, str] = {}
            changes = []
            for torrent in torrents:
                signature = f"{torrent.status}:{torrent.progress:.4f}:{torrent.upload_speed}:{torrent.download_speed}:{torrent.ratio:.3f}"
                current_state[torrent.hash] = signature
                if self._last_torrent_state.get(downloader.id, {}).get(torrent.hash) != signature:
                    changes.append({
                        "hash": torrent.hash,
                        "name": torrent.name,
                        "status": torrent.status,
                        "progress": torrent.progress,
                        "ratio": torrent.ratio,
                        "upload_speed": torrent.upload_speed,
                        "download_speed": torrent.download_speed,
                        "seeding_time": torrent.seeding_time,
                        "size": torrent.size,
                    })

            removed = []
            last_state = self._last_torrent_state.get(downloader.id, {})
            for torrent_hash in last_state:
                if torrent_hash not in current_state:
                    removed.append(torrent_hash)

            if changes or removed:
                await self.manager.broadcast({
                    "type": "torrent_changes",
                    "payload": {
                        "downloader_id": downloader.id,
                        "changes": changes,
                        "removed": removed,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                })

            self._last_torrent_state[downloader.id] = current_state
