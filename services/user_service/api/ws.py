"""WebSocket endpoint for real-time match notifications.

Clients connect with ``?token=<firebase_jwt>`` and receive JSON messages
like ``{"type": "matches_ready"}`` whenever new match results are persisted.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .auth import _decode_jwt_payload

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id] = websocket
        logger.info("WebSocket connected: %s", user_id)

    def disconnect(self, user_id: str) -> None:
        self._connections.pop(user_id, None)
        logger.info("WebSocket disconnected: %s", user_id)

    async def notify_user(self, user_id: str, message: dict) -> None:
        ws = self._connections.get(user_id)
        if ws is None:
            return
        try:
            await ws.send_json(message)
        except Exception:
            logger.warning("Failed to send WS message to %s", user_id)
            self.disconnect(user_id)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        claims = _decode_jwt_payload(token)
        uid = claims.get("user_id") or claims.get("sub")
        if not uid:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(uid, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(uid)
