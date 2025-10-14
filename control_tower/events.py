"""Async event bus for Control Tower."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable


@dataclass
class Event:
    type: str
    payload: dict[str, Any]
    source: str
    id: str | None = None


class EventBus:
    """Simple asyncio-powered pub/sub bus."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._listeners: list[Callable[[Event], Any]] = []

    def publish(self, event: Event) -> None:
        loop = asyncio.get_running_loop()
        self._queue.put_nowait(event)
        for listener in self._listeners:
            if asyncio.iscoroutinefunction(listener):
                loop.create_task(listener(event))
            else:
                loop.run_in_executor(None, listener, event)

    async def subscribe(self) -> AsyncIterator[Event]:
        while True:
            yield await self._queue.get()

    def add_listener(self, listener: Callable[[Event], Any]) -> None:
        self._listeners.append(listener)


__all__ = ["Event", "EventBus"]
