"""WebSocket client for communicating with the Eufy bridge."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Optional

import websockets
from websockets.client import WebSocketClientProtocol


LOGGER = logging.getLogger(__name__)

BridgeEventCallback = Callable[[dict[str, Any]], Awaitable[None]]


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
        self._message_id = 0

    async def connect(self, on_event: BridgeEventCallback) -> None:
        """Start background task maintaining bridge connection."""

        if self._running:
            return
        self._running = True
        self._recv_task = asyncio.create_task(self._run(on_event))

    async def close(self) -> None:
        """Terminate the connection and background task."""

        self._running = False
        async with self._lock:
            if self._ws and not self._ws.closed:
                await self._ws.close()
        if self._recv_task:
            await self._recv_task

    async def send_payload(self, payload: dict[str, Any]) -> None:
        """Send a raw payload to the bridge (messageId optional)."""

        async with self._lock:
            if not self._ws or self._ws.closed:
                raise RuntimeError("BridgeClient not connected")
            await self._ws.send(json.dumps(payload))

    async def request(self, command: str, **params: Any) -> None:
        """Send a command request to the bridge."""

        payload: dict[str, Any] = {
            "command": command,
            "messageId": self._next_message_id(),
        }
        payload.update(params)
        await self.send_payload(payload)

    async def pan_and_tilt(self, serial_number: str, direction: int) -> None:
        await self.request(
            "device.pan_and_tilt",
            serialNumber=serial_number,
            direction=direction,
        )

    async def set_property(self, serial_number: str, name: str, value: Any) -> None:
        await self.request(
            "device.set_property",
            serialNumber=serial_number,
            name=name,
            value=value,
        )

    async def start_livestream(self, serial_number: str) -> None:
        await self.request("device.start_livestream", serialNumber=serial_number)

    async def stop_livestream(self, serial_number: str) -> None:
        await self.request("device.stop_livestream", serialNumber=serial_number)

    async def _run(self, on_event: BridgeEventCallback) -> None:
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
                        normalized = self._normalize_message(data)
                        await on_event(normalized)
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

    def _next_message_id(self) -> int:
        self._message_id += 1
        return self._message_id

    def _normalize_message(self, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {"type": "bridge.raw", "data": data}

        normalized: dict[str, Any] = {"type": "bridge.raw", "data": data}
        msg_type = data.get("type")

        if msg_type == "event":
            event = data.get("event", {})
            event_type = (
                event.get("eventType")
                or event.get("event_type")
                or event.get("name")
                or "event"
            )
            sanitized = str(event_type).replace(":", ".")
            normalized["type"] = f"bridge.event.{sanitized}"
            normalized["event"] = event
        elif msg_type == "result":
            command = data.get("command", "unknown")
            normalized["type"] = f"bridge.result.{command}"
            normalized["result"] = data
        elif msg_type:
            normalized["type"] = f"bridge.{msg_type}"
        return normalized


__all__ = ["BridgeClient"]
