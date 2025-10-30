"""Utility helpers for audio processing and option parsing."""

from __future__ import annotations

import io
import logging
import wave
from typing import Any, Mapping, MutableMapping, Optional

import numpy as np

LOGGER = logging.getLogger(__name__)


def to_wav_bytes(audio: bytes, sample_rate: int, *, channels: int = 1) -> bytes:
    """Convert raw PCM audio bytes into a WAV payload."""
    payload = io.BytesIO()
    with wave.open(payload, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)
    return payload.getvalue()


def rms_amplitude(buffer: bytes) -> float:
    """Compute RMS amplitude for an int16 PCM buffer."""
    if not buffer:
        return 0.0
    samples = np.frombuffer(buffer, dtype=np.int16)
    if samples.size == 0:
        return 0.0
    normalized = samples.astype(np.float32) / 32768.0
    mean_square = float(np.mean(normalized**2))
    return float(np.sqrt(mean_square))


def parse_int(
    options: Mapping[str, Any],
    key: str,
    *,
    default: Optional[int] = None,
    minimum: Optional[int] = None,
) -> Optional[int]:
    value = options.get(key)
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        LOGGER.warning("Invalid int option '%s' for key '%s'", value, key)
        return default
    if minimum is not None and parsed < minimum:
        return minimum
    return parsed


def parse_float(
    options: Mapping[str, Any],
    key: str,
    *,
    default: Optional[float] = None,
) -> Optional[float]:
    value = options.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        LOGGER.warning("Invalid float option '%s' for key '%s'", value, key)
        return default


__all__ = ["to_wav_bytes", "rms_amplitude", "parse_int", "parse_float"]
