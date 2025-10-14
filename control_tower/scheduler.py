"""Async task scheduler for Control Tower."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import List


LOGGER = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    name: str
    interval: float
    coro_factory: Callable[[], Awaitable[None]]
    task: asyncio.Task[None] | None = None


class Scheduler:
    def __init__(self) -> None:
        self._tasks: List[ScheduledTask] = []
        self._running = False

    def register(
        self, name: str, interval: float, coro_factory: Callable[[], Awaitable[None]]
    ) -> None:
        self._tasks.append(ScheduledTask(name, interval, coro_factory))

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        loop = asyncio.get_running_loop()
        for scheduled in self._tasks:
            scheduled.task = loop.create_task(self._loop(scheduled))

    async def stop(self) -> None:
        self._running = False
        for scheduled in self._tasks:
            if scheduled.task:
                scheduled.task.cancel()
                try:
                    await scheduled.task
                except asyncio.CancelledError:
                    pass
                finally:
                    scheduled.task = None

    async def _loop(self, scheduled: ScheduledTask) -> None:
        LOGGER.info(
            "Scheduler task '%s' started (interval %.1fs)",
            scheduled.name,
            scheduled.interval,
        )
        try:
            while self._running:
                await scheduled.coro_factory()
                await asyncio.sleep(scheduled.interval)
        except asyncio.CancelledError:
            LOGGER.info("Scheduler task '%s' cancelled", scheduled.name)
            raise
        except Exception as exc:
            LOGGER.exception("Scheduler task '%s' failed: %s", scheduled.name, exc)
        finally:
            LOGGER.info("Scheduler task '%s' stopped", scheduled.name)
