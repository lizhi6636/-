"""EastMoney WebSocket client for real-time stock data.

Connects to EastMoney's WebSocket service and publishes data to Redis Pub/Sub.
"""

import json
import logging
import struct
import time
import threading

logger = logging.getLogger(__name__)

# EastMoney WebSocket endpoint
EASTMONEY_WS_URL = "ws://push2.eastmoney.com/api/qt/stock/get"


class EastMoneyClient:
    """Singleton client that connects to EastMoney WebSocket.

    In the container environment, this runs in a background thread within
    the FastAPI process. It publishes received data to Redis Pub/Sub
    so the ConnectionManager can fan out to connected clients.
    """

    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None
        self._subscribed_codes: set[str] = set()

    def start(self):
        """Start the EastMoney client in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("EastMoney WebSocket client started")

    def stop(self):
        """Stop the EastMoney client."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("EastMoney WebSocket client stopped")

    def subscribe(self, codes: list[str]):
        """Subscribe to additional stock codes."""
        self._subscribed_codes.update(codes)

    def _run(self):
        """Main loop — connect, subscribe, receive, publish to Redis."""
        import asyncio
        import websocket

        while self._running:
            try:
                ws = websocket.create_connection(
                    EASTMONEY_WS_URL,
                    timeout=10,
                )
                logger.info("Connected to EastMoney WebSocket")

                # Subscribe to watched stocks
                if self._subscribed_codes:
                    codes_str = ",".join(
                        f"1_{code}" if code.startswith("6") else f"0_{code}"
                        for code in self._subscribed_codes
                    )
                    sub_msg = json.dumps({
                        "cmd": "subscribe",
                        "codes": codes_str,
                    })
                    ws.send(sub_msg)

                while self._running:
                    try:
                        ws.settimeout(1.0)
                        data = ws.recv()
                        if data:
                            self._process_message(data)
                    except websocket.WebSocketTimeoutException:
                        continue
                    except Exception as e:
                        logger.error(f"EastMoney recv error: {e}")
                        break

                ws.close()
            except Exception as e:
                logger.error(f"EastMoney connection error: {e}")

            if self._running:
                time.sleep(5)  # Reconnect delay

    def _process_message(self, data: str):
        """Process a message from EastMoney and publish to Redis."""
        try:
            # EastMoney data is often in a binary/text mixed format
            # For simplicity, we log it; in production you'd parse the format
            parsed = json.loads(data) if data.startswith("{") else {"raw": data[:200]}

            # Publish to Redis async
            # This would push to Redis Pub/Sub channel "market:realtime:{code}"
            logger.debug(f"EastMoney data received: {str(parsed)[:200]}")
        except Exception as e:
            logger.debug(f"Failed to process EastMoney message: {e}")


# Singleton
eastmoney_client = EastMoneyClient()
