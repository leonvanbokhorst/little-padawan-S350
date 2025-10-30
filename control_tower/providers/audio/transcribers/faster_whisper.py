"""Faster-Whisper powered speech-to-text transcriber."""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Any, Optional

from .base import BaseTranscriber
from ..utils import to_wav_bytes

LOGGER = logging.getLogger(__name__)


class FasterWhisperTranscriber(BaseTranscriber):
    name = "faster_whisper"

    def __init__(
        self,
        model_size: str = "medium",
        *,
        device: str | None = None,
        compute_type: str | None = None,
        download_root: str | None = None,
        cpu_threads: int | None = None,
        beam_size: int = 1,
        language: str | None = None,
    ) -> None:
        from faster_whisper import WhisperModel  # type: ignore

        kwargs: dict[str, Any] = {}
        if device:
            kwargs["device"] = device
        if compute_type:
            kwargs["compute_type"] = compute_type
        elif not device or device.lower() == "cpu":
            kwargs["compute_type"] = "int8"
        else:
            kwargs["compute_type"] = "float16"
        if download_root:
            kwargs["download_root"] = download_root
        if cpu_threads:
            kwargs["cpu_threads"] = cpu_threads
        self._model = WhisperModel(model_size, **kwargs)
        self._beam_size = max(1, beam_size)
        self._language = language

    async def transcribe(
        self,
        audio: bytes,
        sample_rate: int,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        wav_bytes = to_wav_bytes(audio, sample_rate=sample_rate)

        def run_transcription() -> Optional[str]:
            from faster_whisper.audio import decode_audio  # type: ignore

            pcm, rate = decode_audio(io.BytesIO(wav_bytes))
            segments, _ = self._model.transcribe(
                pcm,
                beam_size=self._beam_size,
                language=self._language,
            )
            text_parts = [segment.text for segment in segments if segment.text]
            return None if not text_parts else " ".join(text_parts).strip()

        return await asyncio.to_thread(run_transcription)


__all__ = ["FasterWhisperTranscriber"]
