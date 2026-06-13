"""WebSocket endpoint for real-time market data."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.ws.manager import manager

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time market data.

    Client sends JSON messages:
    - {"action": "subscribe", "codes": ["000001", "600000"]}
    - {"action": "unsubscribe", "codes": ["000001"]}

    Server pushes:
    - {"code": "000001", "price": 12.34, "change": 0.56, ...}
    """
    # Authenticate via query parameter
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    await manager.connect(websocket, user_id)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                action = msg.get("action")

                if action == "subscribe":
                    codes = msg.get("codes", [])
                    await manager.subscribe(user_id, codes)
                    await manager.send_to_user(user_id, {
                        "type": "subscribed",
                        "codes": codes,
                    })

                elif action == "unsubscribe":
                    codes = msg.get("codes", [])
                    await manager.unsubscribe(user_id, codes)
                    await manager.send_to_user(user_id, {
                        "type": "unsubscribed",
                        "codes": codes,
                    })

                elif action == "ping":
                    await manager.send_to_user(user_id, {"type": "pong"})

                else:
                    await manager.send_to_user(user_id, {
                        "type": "error",
                        "message": f"Unknown action: {action}",
                    })

            except json.JSONDecodeError:
                await manager.send_to_user(user_id, {
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)
