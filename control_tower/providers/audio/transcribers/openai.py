"""OpenAI Whisper API backed STT transcriber."""

from __future__ import annotations

import logging
from typing import Any, Optional

from .base import BaseTranscriber
from ..utils import to_wav_bytes

LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from openai import AsyncOpenAI  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    AsyncOpenAI = None  # type: ignore


class OpenAITranscriber(BaseTranscriber):
    name = "openai"

    def __init__(self, model: str, timeout: float | None = None) -> None:
        if AsyncOpenAI is None:  # pragma: no cover - optional path
            raise RuntimeError("openai package not installed")
        self._client = AsyncOpenAI(timeout=timeout)
        self._model = model

    async def transcribe(
        self,
        audio: bytes,
        sample_rate: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        wav_bytes = to_wav_bytes(audio, sample_rate=sample_rate)
        try:
            response = await self._client.audio.transcriptions.create(  # type: ignore[attr-defined]
                model=self._model,
                file=("chunk.wav", wav_bytes, "audio/wav"),
                response_format="text",
            )
        except Exception as exc:  # pragma: no cover - network errors
            LOGGER.exception("OpenAI transcription failed: %s", exc)
            return None
        text = getattr(response, "text", None)
        return text.strip() if isinstance(text, str) else None


__all__ = ["OpenAITranscriber"]
