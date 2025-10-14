"""WebSocket client for communicating with the Eufy bridge."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Optional

import websockets
from websockets.client import WebSocketClientProtocol


LOGGER = logging.getLogger(__name__)


class BridgeClient:
    """Maintain a persistent WebSocket connection to the Node bridge."""

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        reconnect_delay: float = 3.0,
    ) -> None:
        self.url = url
        self.token = token
        self.reconnect_delay = reconnect_delay
        self._ws: Optional[WebSocketClientProtocol] = None
        self._lock = asyncio.Lock()
        self._recv_task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def connect(
        self, on_event: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Start background task maintaining bridge connection."""

        if self._running:
            return
        self._running = True
        self._recv_task = asyncio.create_task(self._run(on_event))

    async def _run(self, on_event: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        while self._running:
            try:
                LOGGER.info("Connecting to bridge %s", self.url)
                async with websockets.connect(
                    self.url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as ws:
                    async with self._lock:
                        self._ws = ws
                    LOGGER.info("Bridge connected")
                    async for message in ws:
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            LOGGER.warning("Bridge sent non-JSON payload: %s", message)
                            continue
                        await on_event(data)
            except (OSError, websockets.WebSocketException) as exc:
                LOGGER.warning("Bridge connection error: %s", exc)
            finally:
                async with self._lock:
                    self._ws = None
                if self._running:
                    LOGGER.info(
                        "Bridge reconnecting in %.1f seconds", self.reconnect_delay
                    )
                    await asyncio.sleep(self.reconnect_delay)

    async def send_command(self, command: dict[str, Any]) -> None:
        """Send a command to the bridge."""

        async with self._lock:
            if not self._ws or self._ws.closed:
                raise RuntimeError("BridgeClient not connected")
            payload = json.dumps(command)
            await self._ws.send(payload)

    async def close(self) -> None:
        """Terminate the connection and background task."""

        self._running = False
        async with self._lock:
            if self._ws and not self._ws.closed:
                await self._ws.close()
        if self._recv_task:
            await self._recv_task


__all__ = ["BridgeClient"]
