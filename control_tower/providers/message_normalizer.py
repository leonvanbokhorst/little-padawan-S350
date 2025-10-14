"""Utility for normalizing raw bridge messages."""

from __future__ import annotations

from typing import Any, Dict


class MessageNormalizer:
    """Convert bridge responses into a normalized event/result structure."""

    EVENT_PREFIX = "bridge.event."

    @staticmethod
    def normalize(data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            return {"type": "bridge.raw", "data": data}

        msg_type = data.get("type")
        if msg_type == "event":
            event = data.get("event", {})
            key = (
                event.get("eventType")
                or event.get("event_type")
                or event.get("name")
                or event.get("event")
                or "event"
            )
            return {
                "type": MessageNormalizer.EVENT_PREFIX + str(key).replace(":", "."),
                "event": event,
            }
        if msg_type == "result":
            command = data.get("command", "unknown")
            return {
                "type": f"bridge.result.{command}",
                "result": data.get("result", {}),
            }
        if msg_type:
            return {"type": f"bridge.{msg_type}", "data": data}
        return {"type": "bridge.raw", "data": data}


__all__ = ["MessageNormalizer"]
