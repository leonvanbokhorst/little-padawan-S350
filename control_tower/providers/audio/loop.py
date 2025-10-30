"""Audio loop for capturing microphone or remote audio and dispatching STT events."""

from __future__ import annotations

import asyncio
import base64
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

try:  # pragma: no cover - optional dependency
    import sounddevice as sd  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    sd = None  # type: ignore

from control_tower.config import ProviderConfig
from control_tower.events import Event, EventBus
from control_tower.providers.audio.stt_factory import build_transcriber
from control_tower.providers.audio.transcribers import BaseTranscriber
from control_tower.providers.audio.utils import rms_amplitude

LOGGER = logging.getLogger(__name__)

_HOST_SOURCE = "host"
_BRIDGE_SOURCE = "bridge"
_DISABLED_SOURCE = "disabled"


@dataclass
class AudioLoopState:
    available: bool
    running: bool
    has_transcription: bool
    source: str


class AudioLoop:
    def __init__(
        self,
        event_bus: EventBus,
        stt_config: ProviderConfig,
        *,
        audio_source: str = _HOST_SOURCE,
        sample_rate: int = 16_000,
        chunk_seconds: float = 2.0,
        vad_threshold: float = 0.015,
        queue_size: int = 32,
    ) -> None:
        self.event_bus = event_bus
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.vad_threshold = vad_threshold
        self.audio_source = (audio_source or _HOST_SOURCE).lower()
        self._bytes_per_sample = 2
        self._chunk_bytes = int(self.sample_rate * self.chunk_seconds * self._bytes_per_sample)
        self._frame_queue: queue.Queue[bytes] = queue.Queue(maxsize=queue_size)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._processor_task: Optional[asyncio.Task[None]] = None
        self._thread: Optional[threading.Thread] = None
        self._stream: Any = None
        self._running = False
        self._transcriber: BaseTranscriber = build_transcriber(stt_config)
        self._available = self._detect_availability(stt_config)
        self._last_transcription: Optional[dict[str, Any]] = None

    @property
    def available(self) -> bool:
        return self._available

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_transcription(self) -> Optional[dict[str, Any]]:
        return self._last_transcription

    def snapshot(self) -> AudioLoopState:
        return AudioLoopState(
            available=self.available,
            running=self.is_running,
            has_transcription=self._last_transcription is not None,
            source=self.audio_source,
        )

    async def start(self) -> None:
        if not self._available:
            LOGGER.info("Audio loop not available; skipping start")
            return
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_running_loop()
        if self.audio_source == _HOST_SOURCE:
            self._processor_task = asyncio.create_task(self._process_frames())
            self._thread = threading.Thread(target=self._run_stream, name="audio-loop", daemon=True)
            self._thread.start()
            LOGGER.info("Audio loop started (host microphone)")
        elif self.audio_source == _BRIDGE_SOURCE:
            LOGGER.info("Audio loop started (bridge input)")
        else:
            LOGGER.info("Audio loop started (source=%s)", self.audio_source)

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            finally:
                self._processor_task = None
        if self._thread:
            self._thread.join(timeout=1.5)
            self._thread = None
        LOGGER.info("Audio loop stopped")

    def ingest_remote_chunk(
        self,
        chunk: bytes | str,
        *,
        sample_rate: Optional[int] = None,
        rms: Optional[float] = None,
        duration: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
        encoded: bool = False,
    ) -> None:
        if self.audio_source != _BRIDGE_SOURCE:
            LOGGER.debug("Ignoring remote chunk because source=%s", self.audio_source)
            return
        if encoded:
            try:
                chunk = base64.b64decode(chunk, validate=True)
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.warning("Failed to decode bridge audio chunk: %s", exc)
                return
        sr = sample_rate or self.sample_rate
        calculated_rms = rms if rms is not None else rms_amplitude(chunk)
        calculated_duration = (
            duration
            if duration is not None
            else len(chunk) / (sr * self._bytes_per_sample)
        )
        if calculated_rms < self.vad_threshold:
            self._publish_chunk_skipped(
                reason="vad_threshold",
                rms=calculated_rms,
                duration=calculated_duration,
                provider=self._transcriber.name,
                source=_BRIDGE_SOURCE,
            )
            return
        if not self._loop:
            LOGGER.debug("Remote chunk received before loop start; dropping")
            return
        self._loop.create_task(
            self._handle_chunk(
                chunk,
                sample_rate=sr,
                rms=calculated_rms,
                duration=calculated_duration,
                metadata=(metadata or {}) | {"source": _BRIDGE_SOURCE},
            )
        )

    def handle_bridge_event(self, message: dict[str, Any]) -> None:
        """Attempt to ingest raw audio payloads coming from the bridge."""

        if self.audio_source != _BRIDGE_SOURCE:
            return
        if not isinstance(message, dict):
            return

        payload = message.get("event") if isinstance(message.get("event"), dict) else message
        if not isinstance(payload, dict):
            return

        audio_section = payload.get("audio") if isinstance(payload.get("audio"), dict) else None
        candidate = audio_section or payload
        if not isinstance(candidate, dict):
            return

        chunk_data = candidate.get("pcm_base64")
        encoded = True
        if chunk_data is None:
            chunk_data = candidate.get("audio_base64")
        if chunk_data is None:
            chunk_data = candidate.get("audioChunk")
        if chunk_data is None:
            chunk_data = candidate.get("pcm")
            encoded = False
        if chunk_data is None:
            return

        def _to_int(value: Any) -> Optional[int]:
            if value is None:
                return None
            if isinstance(value, int):
                return value
            try:
                return int(value)
            except (TypeError, ValueError):
                LOGGER.debug("Invalid int value from bridge payload: %s", value)
                return None

        def _to_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            try:
                return float(value)
            except (TypeError, ValueError):
                LOGGER.debug("Invalid float value from bridge payload: %s", value)
                return None

        sample_rate = _to_int(
            candidate.get("sample_rate")
            or candidate.get("sampleRate")
            or payload.get("sample_rate")
            or payload.get("sampleRate")
        )
        duration = _to_float(candidate.get("duration") or payload.get("duration"))
        rms = _to_float(candidate.get("rms") or payload.get("rms"))

        metadata = {
            key: candidate.get(key)
            for key in ("sequence", "chunk_id", "channel")
            if candidate.get(key) is not None
        }

        self.ingest_remote_chunk(
            chunk_data,
            sample_rate=sample_rate,
            rms=rms,
            duration=duration,
            metadata=metadata or None,
            encoded=encoded and isinstance(chunk_data, str),
        )

    def _detect_availability(self, config: ProviderConfig) -> bool:
        if self.audio_source == _DISABLED_SOURCE:
            LOGGER.info("Audio loop disabled via audio_source=disabled")
            return False
        if self.audio_source == _BRIDGE_SOURCE:
            return True
        if sd is None:
            LOGGER.warning(
                "Audio loop unavailable: sounddevice package not installed. Install sounddevice/PortAudio."
            )
            return False
        try:
            sd.query_devices(kind="input")
        except Exception as exc:  # pragma: no cover - hardware dependent
            LOGGER.warning("Audio loop unavailable: no input device (%s)", exc)
            return False
        return True

    def _run_stream(self) -> None:
        if sd is None:
            return
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                callback=self._on_audio_frame,
            ) as stream:
                self._stream = stream
                while self._running:
                    time.sleep(0.1)
        except Exception as exc:  # pragma: no cover - hardware dependent
            LOGGER.exception("Audio capture error: %s", exc)
            if self._loop:
                self._loop.call_soon_threadsafe(self._publish_error, str(exc))
        finally:
            self._stream = None

    def _on_audio_frame(self, indata, frames, time_info, status) -> None:  # pragma: no cover - callback
        if not self._running:
            return
        if status:
            LOGGER.debug("Audio callback status: %s", status)
        try:
            data = bytes(indata.tobytes())
            self._frame_queue.put_nowait(data)
        except queue.Full:
            LOGGER.warning("Audio frame queue full; dropping chunk")

    async def _process_frames(self) -> None:
        buffer = bytearray()
        loop = asyncio.get_running_loop()
        try:
            while self._running or not self._frame_queue.empty():
                try:
                    frame = await asyncio.to_thread(self._frame_queue.get, timeout=0.5)
                except queue.Empty:
                    continue
                buffer.extend(frame)
                if len(buffer) < self._chunk_bytes:
                    continue
                chunk = bytes(buffer[: self._chunk_bytes])
                del buffer[: self._chunk_bytes]
                rms = rms_amplitude(chunk)
                duration = len(chunk) / (self.sample_rate * self._bytes_per_sample)
                if rms < self.vad_threshold:
                    self._publish_chunk_skipped(
                        reason="vad_threshold",
                        rms=rms,
                        duration=duration,
                        provider=self._transcriber.name,
                        source=_HOST_SOURCE,
                    )
                    continue
                await self._handle_chunk(
                    chunk,
                    sample_rate=self.sample_rate,
                    rms=rms,
                    duration=duration,
                    metadata={"source": _HOST_SOURCE},
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected
            LOGGER.exception("Audio processing loop failed: %s", exc)
            loop.call_soon_threadsafe(self._publish_error, str(exc))

    async def _handle_chunk(
        self,
        chunk: bytes,
        *,
        sample_rate: int,
        rms: float,
        duration: float,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        metadata = metadata or {}
        metadata.setdefault("rms", rms)
        metadata.setdefault("duration", duration)
        metadata.setdefault("source", self.audio_source)
        try:
            text = await self._transcriber.transcribe(chunk, sample_rate, metadata)
        except Exception as exc:  # pragma: no cover - provider errors
            LOGGER.exception("Transcription failed: %s", exc)
            self._publish_error(f"transcriber error: {exc}")
            return
        if not text:
            self._publish_chunk_skipped(
                reason="empty_transcription",
                rms=rms,
                duration=duration,
                provider=self._transcriber.name,
                source=metadata.get("source", self.audio_source),
            )
            return
        timestamp = time.time()
        payload = {
            "text": text,
            "duration": duration,
            "rms": rms,
            "provider": self._transcriber.name,
            "timestamp": timestamp,
            "source": metadata.get("source", self.audio_source),
        }
        self._last_transcription = payload
        self.event_bus.publish(
            Event(
                type="audio.transcription",
                payload=payload,
                source="audio",
            )
        )

    def _publish_error(self, message: str) -> None:
        if not self.event_bus:
            return
        self.event_bus.publish(
            Event(
                type="audio.error",
                payload={"message": message},
                source="audio",
            )
        )

    def _publish_chunk_skipped(
        self,
        *,
        reason: str,
        rms: float,
        duration: float,
        provider: str,
        source: str,
    ) -> None:
        LOGGER.info(
            "Audio chunk skipped (%s): rms=%.3f duration=%.2fs provider=%s source=%s",
            reason,
            rms,
            duration,
            provider,
            source,
        )
        if not self.event_bus:
            return
        self.event_bus.publish(
            Event(
                type="audio.chunk_skipped",
                payload={
                    "reason": reason,
                    "rms": rms,
                    "duration": duration,
                    "provider": provider,
                    "source": source,
                    "timestamp": time.time(),
                },
                source="audio",
            )
        )


__all__ = ["AudioLoop", "AudioLoopState"]
