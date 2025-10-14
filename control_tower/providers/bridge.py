"""WebSocket client stub for communicating with the Eufy bridge."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Optional


class BridgeClient:
    def __init__(self, url: str, token: Optional[str] = None) -> None:
        self.url = url
        self.token = token
        self._connected = False

    async def connect(self) -> None:
        # TODO: Implement actual WebSocket connection.
        await asyncio.sleep(0)
        self._connected = True

    async def send_command(self, command: dict[str, Any]) -> None:
        if not self._connected:
            raise RuntimeError("BridgeClient not connected")
        payload = json.dumps(command)
        # TODO: send via WebSocket
        await asyncio.sleep(0)
        print(f"[BridgeClient] send {payload}")

    async def subscribe_events(
        self, callback: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        if not self._connected:
            raise RuntimeError("BridgeClient not connected")
        while True:
            await asyncio.sleep(1)
            await callback({"type": "bridge.heartbeat"})


__all__ = ["BridgeClient"]
