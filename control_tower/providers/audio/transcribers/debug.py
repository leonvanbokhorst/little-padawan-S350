"""Debug transcriber that echoes metadata."""

from __future__ import annotations

from typing import Any, Optional

from .base import BaseTranscriber


class DebugTranscriber(BaseTranscriber):
    name = "debug"

    async def transcribe(
        self,
        audio: bytes,
        sample_rate: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        metadata = metadata or {}
        duration = metadata.get("duration", 0.0)
        rms = metadata.get("rms", 0.0)
        source = metadata.get("source", "?")
        return f"[audio chunk ~{duration:.2f}s, rms={rms:.3f}, source={source}]"


__all__ = ["DebugTranscriber"]
