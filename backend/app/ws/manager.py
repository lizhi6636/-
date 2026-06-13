"""WebSocket connection manager for real-time market data."""

import json
import logging
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and subscriptions."""

    def __init__(self):
        # user_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # stock_code -> set of user_ids
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WS client connected: {user_id}")

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        # Remove user from all subscriptions
        for code in list(self.subscriptions.keys()):
            self.subscriptions[code].discard(user_id)
            if not self.subscriptions[code]:
                del self.subscriptions[code]
        logger.info(f"WS client disconnected: {user_id}")

    async def subscribe(self, user_id: str, codes: list[str]):
        """Subscribe user to stock codes."""
        for code in codes:
            if code not in self.subscriptions:
                self.subscriptions[code] = set()
            self.subscriptions[code].add(user_id)

    async def unsubscribe(self, user_id: str, codes: list[str]):
        """Unsubscribe user from stock codes."""
        for code in codes:
            if code in self.subscriptions:
                self.subscriptions[code].discard(user_id)

    async def broadcast_to_code(self, code: str, data: dict):
        """Send data to all users subscribed to a stock code."""
        if code not in self.subscriptions:
            return

        message = json.dumps(data, ensure_ascii=False)
        disconnected = []
        for user_id in self.subscriptions[code]:
            ws = self.active_connections.get(user_id)
            if ws:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(user_id)

        for uid in disconnected:
            self.disconnect(uid)

    async def send_to_user(self, user_id: str, data: dict):
        """Send data to a specific user."""
        ws = self.active_connections.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                self.disconnect(user_id)


manager = ConnectionManager()
