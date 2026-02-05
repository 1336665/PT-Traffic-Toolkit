from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.database import async_session_maker
from app.models import User
from app.services.auth import decode_token
from app.services.realtime import RealtimeConnectionManager, RealtimeBroadcaster


router = APIRouter(prefix="/ws", tags=["WebSocket"])

manager = RealtimeConnectionManager()
broadcaster = RealtimeBroadcaster(manager)


async def _authenticate(token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_token(token)
    if payload is None:
        return None
    username = payload.get("sub")
    if not username:
        return None
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()


@router.websocket("/realtime")
async def realtime_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    user = await _authenticate(token)
    if not user:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    await broadcaster.start()

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
