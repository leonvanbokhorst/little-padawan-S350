"""Vision loop stub emitting motion events."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .events import EventBus, Event


LOGGER = logging.getLogger(__name__)


class VisionLoop:
    def __init__(
        self, event_bus: EventBus, interval: float = 5.0, enabled: bool = True
    ) -> None:
        self.event_bus = event_bus
        self.interval = interval
        self.enabled = enabled
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    async def start(self) -> None:
        if self._running or not self.enabled:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        LOGGER.info("Vision loop stub running (interval %.1fs)", self.interval)
        try:
            while self._running:
                await asyncio.sleep(self.interval)
                self.event_bus.publish(
                    Event(
                        type="vision.motion",
                        payload={"confidence": 0.1, "note": "stub"},
                        source="vision",
                    )
                )
        finally:
            LOGGER.info("Vision loop stopped")


__all__ = ["VisionLoop"]
