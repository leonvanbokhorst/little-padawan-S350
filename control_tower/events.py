"""Async event bus for Control Tower."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional


@dataclass
class Event:
    type: str
    payload: Dict[str, Any]
    source: str
    id: Optional[str] = None


class EventBus:
    """Simple asyncio-powered pub/sub bus."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()

    def publish(self, event: Event) -> None:
        self._queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[Event]:
        while True:
            event = await self._queue.get()
            yield event


__all__ = ["Event", "EventBus"]
