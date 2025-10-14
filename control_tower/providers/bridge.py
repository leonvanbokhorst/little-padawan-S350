"""WebSocket client for communicating with the Eufy bridge."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets


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
        self._ws = None
        self._lock = asyncio.Lock()
        self._recv_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._message_id = 0
        self._devices: dict[str, dict[str, Any]] = {}
        self._ready = asyncio.Event()

    @property
    def devices(self) -> Dict[str, Dict[str, Any]]:
        return copy.deepcopy(self._devices)

    async def wait_until_ready(self, timeout: float | None = None) -> None:
        if timeout is None:
            await self._ready.wait()
        else:
            await asyncio.wait_for(self._ready.wait(), timeout)

    async def connect(self, on_event: BridgeEventCallback) -> None:
        if self._running:
            return
        self._running = True
        self._recv_task = asyncio.create_task(self._run(on_event))

    async def close(self) -> None:
        self._running = False
        self._ready.clear()
        async with self._lock:
            ws = self._ws
            self._ws = None
        if ws:
            await ws.close()
        if self._recv_task:
            await self._recv_task
            self._recv_task = None

    async def start_listening(
        self, *, connect_cloud: bool = True, poll_refresh: bool = True
    ) -> None:
        await self.wait_until_ready()
        await self.request("start_listening")
        if connect_cloud:
            await self.request("driver.connect")
        if poll_refresh:
            await self.request("driver.poll_refresh")

    async def ensure_station_metadata(
        self, serial_number: str, *, include_metadata: bool = True
    ) -> None:
        await self.wait_until_ready()
        await self.request("station.connect", serialNumber=serial_number)
        await self.request("station.get_properties", serialNumber=serial_number)
        if include_metadata:
            await self.request(
                "station.get_properties_metadata", serialNumber=serial_number
            )

    async def send_payload(self, payload: dict[str, Any]) -> None:
        try:
            await self.wait_until_ready(timeout=10)
        except asyncio.TimeoutError as exc:
            raise RuntimeError("BridgeClient not connected") from exc
        async with self._lock:
            if not self._ws:
                raise RuntimeError("BridgeClient not connected")
            await self._ws.send(json.dumps(payload))

    async def request(self, command: str, **params: Any) -> None:
        payload: dict[str, Any] = {
            "command": command,
            "messageId": self._next_message_id(),
        }
        payload.update(params)
        LOGGER.debug("Bridge request %s", payload)
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
                    additional_headers=headers if headers else None,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as ws:
                    async with self._lock:
                        self._ws = ws
                        self._ready.set()
                    LOGGER.info("Bridge connected")
                    async for message in ws:
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            LOGGER.warning("Bridge sent non-JSON payload: %s", message)
                            continue
                        normalized = self._normalize_message(data)
                        self._track_devices(normalized)
                        await on_event(normalized)
            except (OSError, websockets.WebSocketException) as exc:
                LOGGER.warning("Bridge connection error: %s", exc)
            finally:
                self._ready.clear()
                async with self._lock:
                    self._ws = None
                if self._running:
                    LOGGER.info(
                        "Bridge reconnecting in %.1f seconds", self.reconnect_delay
                    )
                    await asyncio.sleep(self.reconnect_delay)

    def _track_devices(self, message: dict[str, Any]) -> None:
        result = message.get("result")
        if isinstance(result, dict):
            serial = result.get("serialNumber") or result.get("deviceSerialNumber")
            if serial:
                device = self._devices.setdefault(serial, {})
                props = result.get("properties")
                if isinstance(props, dict):
                    device.setdefault("properties", {}).update(props)
                metadata = result.get("propertiesMetadata") or result.get("metadata")
                if isinstance(metadata, dict):
                    device.setdefault("propertiesMetadata", {}).update(metadata)
        event = message.get("event")
        if isinstance(event, dict):
            serial = (
                event.get("serialNumber") or event.get("device") or event.get("station")
            )
            if serial:
                device = self._devices.setdefault(serial, {})
                device.setdefault("events", []).append(event)

    def _next_message_id(self) -> str:
        self._message_id += 1
        return str(self._message_id)

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
                or event.get("event")
                or "event"
            )
            sanitized = str(event_type).replace(":", ".")
            normalized["type"] = f"bridge.event.{sanitized}"
            normalized["event"] = event
        elif msg_type == "result":
            command = data.get("command", "unknown")
            normalized["type"] = f"bridge.result.{command}"
            normalized["result"] = data.get("result", {})
        elif msg_type:
            normalized["type"] = f"bridge.{msg_type}"
        return normalized


__all__ = ["BridgeClient"]
