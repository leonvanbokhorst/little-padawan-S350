"""Vision loop consuming RTSP frames and emitting motion events."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

try:
    import cv2  # type: ignore
    import numpy as np
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore
    np = None  # type: ignore

from .events import EventBus, Event


LOGGER = logging.getLogger(__name__)


class VisionLoop:
    """Process frames from RTSP and emit motion events."""

    def __init__(
        self,
        event_bus: EventBus,
        rtsp_url: Optional[str],
        poll_interval: float = 0.2,
        motion_threshold: int = 5000,
        cooldown: float = 2.0,
    ) -> None:
        self.event_bus = event_bus
        self.rtsp_url = rtsp_url
        self.poll_interval = poll_interval
        self.motion_threshold = motion_threshold
        self.cooldown = cooldown
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._last_motion: float = 0.0

        if not rtsp_url:
            LOGGER.info("Vision loop disabled: RTSP URL missing")
            self._available = False
        elif cv2 is None or np is None:
            LOGGER.warning(
                "Vision loop disabled: OpenCV or NumPy not available. Install opencv-python-headless & numpy."
            )
            self._available = False
        else:
            self._available = True

    async def start(self) -> None:
        if self._running or not self._available:
            return
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            finally:
                self._task = None
        self._loop = None

    async def _run(self) -> None:
        LOGGER.info("Vision loop starting for RTSP stream: %s", self.rtsp_url)
        try:
            await asyncio.to_thread(self._capture_loop)
        finally:
            LOGGER.info("Vision loop stopped")

    def _capture_loop(self) -> None:
        assert cv2 is not None and np is not None
        cap: Optional[cv2.VideoCapture] = None  # type: ignore[assignment]
        prev_frame: Optional[np.ndarray] = None
        last_processed = 0.0

        while self._running:
            if cap is None or not cap.isOpened():
                if cap is not None:
                    cap.release()
                cap = cv2.VideoCapture(self.rtsp_url)  # type: ignore[arg-type]
                if not cap.isOpened():
                    LOGGER.warning(
                        "Vision loop: unable to open RTSP stream; retrying in 5s"
                    )
                    self._sleep(5)
                    cap = None
                    continue
                LOGGER.info("Vision loop connected to RTSP stream")
                prev_frame = None
                last_processed = 0.0

            ret, frame = cap.read()
            if not ret:
                LOGGER.warning(
                    "Vision loop: failed to read frame; restarting after short pause"
                )
                self._sleep(1)
                cap.release()
                cap = None
                continue

            now = time.time()
            if now - last_processed < self.poll_interval:
                continue
            last_processed = now

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            if prev_frame is None:
                prev_frame = gray
                continue

            diff = cv2.absdiff(prev_frame, gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            motion_pixels = int(np.count_nonzero(thresh))
            total_pixels = thresh.size
            motion_ratio = motion_pixels / total_pixels if total_pixels else 0
            prev_frame = gray

            if motion_pixels >= self.motion_threshold:
                if now - self._last_motion >= self.cooldown:
                    self._emit_motion_event(motion_pixels, motion_ratio)
                    self._last_motion = now

        if cap is not None:
            cap.release()

    def _emit_motion_event(self, pixels: int, ratio: float) -> None:
        if not self._loop:
            return
        event = Event(
            type="vision.motion",
            payload={
                "motion_pixels": pixels,
                "motion_ratio": ratio,
                "threshold": self.motion_threshold,
            },
            source="vision",
        )
        self._loop.call_soon_threadsafe(self.event_bus.publish, event)

    def _sleep(self, seconds: float) -> None:
        end = time.time() + seconds
        while self._running and time.time() < end:
            time.sleep(0.2)


__all__ = ["VisionLoop"]
