"""Device registry for tracking bridge metadata and events."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict


@dataclass
class DeviceRecord:
    serial: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    events: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=200))


class DeviceRegistry:
    """Maintain device metadata with a bounded history to avoid memory creep."""

    def __init__(self, event_history: int = 200) -> None:
        self._devices: Dict[str, DeviceRecord] = {}
        self._event_history = event_history

    @property
    def devices(self) -> Dict[str, Dict[str, Any]]:
        snapshot: Dict[str, Dict[str, Any]] = {}
        for serial, record in self._devices.items():
            snapshot[serial] = {
                "properties": dict(record.properties),
                "propertiesMetadata": dict(record.metadata),
                "events": list(record.events),
            }
        return snapshot

    def update_from_result(self, payload: Dict[str, Any]) -> None:
        serial = payload.get("serialNumber") or payload.get("deviceSerialNumber")
        if not serial:
            return
        record = self._devices.setdefault(serial, DeviceRecord(serial))
        if isinstance(payload.get("properties"), dict):
            record.properties.update(payload["properties"])
        metadata = payload.get("propertiesMetadata") or payload.get("metadata")
        if isinstance(metadata, dict):
            record.metadata.update(metadata)

    def update_from_event(self, payload: Dict[str, Any]) -> None:
        serial = (
            payload.get("serialNumber")
            or payload.get("device")
            or payload.get("station")
        )
        if not serial:
            return
        record = self._devices.setdefault(serial, DeviceRecord(serial))
        if record.events.maxlen != self._event_history:
            record.events = deque(record.events, maxlen=self._event_history)
        record.events.append(payload)


__all__ = ["DeviceRegistry"]
