"""Factory helpers for building STT transcribers."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from control_tower.config import ProviderConfig
from control_tower.providers.audio.transcribers import (
    BaseTranscriber,
    DebugTranscriber,
    FasterWhisperTranscriber,
    OpenAITranscriber,
)
from control_tower.providers.audio.utils import parse_float, parse_int

try:  # pragma: no cover - optional dependency
    from openai import AsyncOpenAI  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    AsyncOpenAI = None  # type: ignore

LOGGER = logging.getLogger(__name__)


_FASTER_WHISPER_ALIASES = {"faster-whisper", "faster_whisper", "whisper"}
_OPENAI_ALIASES = {"openai", "gpt"}


def build_transcriber(config: ProviderConfig) -> BaseTranscriber:
    kind = (config.kind or "").lower()
    options: Mapping[str, Any] = config.options or {}

    if kind in _FASTER_WHISPER_ALIASES:
        return _build_faster_whisper(options)

    if kind in _OPENAI_ALIASES:
        return _build_openai(options, kind)

    if kind == "disabled":
        LOGGER.info("STT provider disabled via configuration")
        return DebugTranscriber()

    if kind:
        LOGGER.warning("Unknown STT provider '%s'; using debug transcriber", kind)
    return DebugTranscriber()


def _build_faster_whisper(options: Mapping[str, Any]) -> BaseTranscriber:
    model_size = options.get("model", "base")
    device = options.get("device")
    compute_type = options.get("compute_type")
    download_root = options.get("download_root")
    cpu_threads = parse_int(options, "cpu_threads")
    beam_size = parse_int(options, "beam_size", default=1, minimum=1) or 1
    language = options.get("language")

    try:
        return FasterWhisperTranscriber(
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            download_root=download_root,
            cpu_threads=cpu_threads,
            beam_size=beam_size,
            language=language,
        )
    except Exception as exc:  # pragma: no cover - model load errors
        LOGGER.exception("Failed to initialize FasterWhisper model: %s", exc)
        LOGGER.warning("Falling back to debug transcriber")
        return DebugTranscriber()


def _build_openai(options: Mapping[str, Any], kind: str) -> BaseTranscriber:
    model = options.get("model", "gpt-4o-mini-transcribe")
    timeout = parse_float(options, "timeout")

    if AsyncOpenAI is None:
        LOGGER.warning(
            "STT provider '%s' requested but openai package not installed. Using debug transcriber.",
            kind,
        )
        return DebugTranscriber()

    try:
        return OpenAITranscriber(model=model, timeout=timeout)
    except RuntimeError as exc:  # pragma: no cover - optional path
        LOGGER.warning("OpenAI transcriber initialization failed: %s", exc)
        return DebugTranscriber()


__all__ = ["build_transcriber"]
