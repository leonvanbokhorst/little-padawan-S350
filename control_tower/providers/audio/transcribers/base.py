"""Base class for speech-to-text transcribers."""

from __future__ import annotations

from typing import Any, Optional


class BaseTranscriber:
    """Abstract interface for pluggable STT providers."""

    name = "base"

    async def transcribe(
        self,
        audio: bytes,
        sample_rate: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        raise NotImplementedError


__all__ = ["BaseTranscriber"]
