"""Audio loop for capturing microphone or mech audio and dispatching STT events."""

from __future__ import annotations

import asyncio
import io
import logging
import queue
import threading
import time
import wave
from dataclasses import dataclass
from typing import Any, Optional

try:  # pragma: no cover - optional dependency
    import sounddevice as sd
except ImportError:  # pragma: no cover - handled gracefully
    sd = None  # type: ignore

import numpy as np

try:  # pragma: no cover - optional dependency
    from openai import AsyncOpenAI  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully
    AsyncOpenAI = None  # type: ignore

from ..config import ProviderConfig
from ..events import Event, EventBus


LOGGER = logging.getLogger(__name__)


def _rms_amplitude(buffer: bytes) -> float:
    if not buffer:
        return 0.0
    samples = np.frombuffer(buffer, dtype=np.int16)
    if samples.size == 0:
        return 0.0
    normalized = samples.astype(np.float32) / 32768.0
    mean_square = float(np.mean(normalized**2))
    return float(np.sqrt(mean_square))


def _to_wav_bytes(audio: bytes, *, sample_rate: int, channels: int = 1) -> bytes:
    payload = io.BytesIO()
    with wave.open(payload, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)
    return payload.getvalue()


class BaseTranscriber:
    name = "base"

    async def transcribe(
        self, audio: bytes, sample_rate: int, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        raise NotImplementedError


class DebugTranscriber(BaseTranscriber):
    name = "debug"

    async def transcribe(
        self, audio: bytes, sample_rate: int, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        if not metadata:
            metadata = {}
        duration = metadata.get("duration", 0.0)
        rms = metadata.get("rms", 0.0)
        return f"[audio chunk ~{duration:.2f}s, rms={rms:.3f}]"


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
        else:
            if not device or device.lower() == "cpu":
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
        self, audio: bytes, sample_rate: int, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        wav_bytes = _to_wav_bytes(audio, sample_rate=sample_rate)

        def run_transcription() -> Optional[str]:
            from faster_whisper.audio import decode_audio  # type: ignore

            pcm, rate = decode_audio(io.BytesIO(wav_bytes))
            segments, _ = self._model.transcribe(
                pcm,
                beam_size=self._beam_size,
                language=self._language,
            )
            text_parts = [segment.text for segment in segments if segment.text]
            if not text_parts:
                return None
            return " ".join(text_parts).strip()

        return await asyncio.to_thread(run_transcription)


class OpenAITranscriber(BaseTranscriber):
    name = "openai"

    def __init__(self, model: str, timeout: float | None = None) -> None:
        if AsyncOpenAI is None:  # pragma: no cover - optional path
            raise RuntimeError("openai package not installed")
        self._client = AsyncOpenAI(timeout=timeout)
        self._model = model

    async def transcribe(
        self, audio: bytes, sample_rate: int, metadata: Optional[dict[str, Any]] = None
    ) -> Optional[str]:
        wav_bytes = _to_wav_bytes(audio, sample_rate=sample_rate)
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


def _build_transcriber(config: ProviderConfig) -> BaseTranscriber:
    kind = (config.kind or "").lower()
    if kind in {"faster-whisper", "faster_whisper", "whisper"}:
        model_size = config.options.get("model", "base")
        device = config.options.get("device")
        compute_type = config.options.get("compute_type")
        download_root = config.options.get("download_root", ".control_tower/models")
        cpu_threads_raw = config.options.get("cpu_threads")
        beam_size_raw = config.options.get("beam_size")
        language = config.options.get("language")
        cpu_threads: int | None = None
        beam_size = 1
        if cpu_threads_raw is not None:
            try:
                cpu_threads = int(cpu_threads_raw)
            except ValueError:
                LOGGER.warning("Invalid cpu_threads option '%s'", cpu_threads_raw)
        if beam_size_raw is not None:
            try:
                beam_size = max(1, int(beam_size_raw))
            except ValueError:
                LOGGER.warning("Invalid beam_size option '%s'", beam_size_raw)
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
    elif kind in {"openai", "gpt"}:
        model = config.options.get("model", "gpt-4o-mini-transcribe")
        timeout_raw = config.options.get("timeout")
        timeout: float | None = None
        if timeout_raw is not None:
            try:
                timeout = float(timeout_raw)
            except ValueError:
                LOGGER.warning("Invalid timeout option '%s'", timeout_raw)
        if AsyncOpenAI is None:
            LOGGER.warning(
                "STT provider '%s' requested but openai package not installed. Using debug transcriber.",
                config.kind,
            )
        else:
            try:
                return OpenAITranscriber(model=model, timeout=timeout)
            except RuntimeError as exc:  # pragma: no cover - optional path
                LOGGER.warning("OpenAI transcriber initialization failed: %s", exc)
    if kind == "disabled":
        LOGGER.info("STT provider disabled via configuration")
        return DebugTranscriber()
    return DebugTranscriber()


@dataclass
class AudioLoopState:
    available: bool
    running: bool
    last_transcription: Optional[dict[str, Any]]


class AudioLoop:
    def __init__(
        self,
        event_bus: EventBus,
        stt_config: ProviderConfig,
        *,
        sample_rate: int = 16_000,
        chunk_seconds: float = 2.0,
        vad_threshold: float = 0.015,
        queue_size: int = 32,
    ) -> None:
        self.event_bus = event_bus
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.vad_threshold = vad_threshold
        self._bytes_per_sample = 2
        self._chunk_bytes = int(
            self.sample_rate * self.chunk_seconds * self._bytes_per_sample
        )
        self._frame_queue: queue.Queue[bytes] = queue.Queue(maxsize=queue_size)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._processor_task: Optional[asyncio.Task[None]] = None
        self._thread: Optional[threading.Thread] = None
        self._stream: Any = None
        self._running = False
        self._available = self._detect_availability(stt_config)
        self._transcriber = _build_transcriber(stt_config)
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
            last_transcription=self._last_transcription,
        )

    async def start(self) -> None:
        if not self._available:
            LOGGER.info("Audio loop not available; skipping start")
            return
        if self._running:
            return
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._processor_task = asyncio.create_task(self._process_frames())
        self._thread = threading.Thread(
            target=self._run_stream, name="audio-loop", daemon=True
        )
        self._thread.start()
        LOGGER.info("Audio loop started")

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

    def _detect_availability(self, config: ProviderConfig) -> bool:
        kind = (config.kind or "").lower()
        if kind == "disabled":
            LOGGER.info("Audio loop disabled due to STT provider=disabled")
            return False
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

    def _on_audio_frame(
        self, indata, frames, time_info, status
    ) -> None:  # pragma: no cover - callback
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
                rms = _rms_amplitude(chunk)
                if rms < self.vad_threshold:
                    continue
                duration = len(chunk) / (self.sample_rate * self._bytes_per_sample)
                await self._handle_chunk(chunk, rms=rms, duration=duration)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover - unexpected
            LOGGER.exception("Audio processing loop failed: %s", exc)
            loop.call_soon_threadsafe(self._publish_error, str(exc))

    async def _handle_chunk(self, chunk: bytes, *, rms: float, duration: float) -> None:
        metadata = {"rms": rms, "duration": duration}
        text: Optional[str]
        try:
            text = await self._transcriber.transcribe(chunk, self.sample_rate, metadata)
        except Exception as exc:  # pragma: no cover - provider errors
            LOGGER.exception("Transcription failed: %s", exc)
            self._publish_error(f"transcriber error: {exc}")
            return
        if not text:
            LOGGER.info("Audio chunk skipped: empty transcription (silent or low VAD). RMS: %.2f, duration: %.2f", rms, duration)
            self.event_bus.publish(
                Event(
                    type="audio_chunk_skipped",
                    payload={
                        "reason": "empty_transcription",
                        "rms": rms,
                        "duration": duration,
                        "provider": self._transcriber.name,
                        "timestamp": time.time(),
                    },
                )
            )
            return
        timestamp = time.time()
        payload = {
            "text": text,
            "duration": duration,
            "rms": rms,
            "provider": self._transcriber.name,
            "timestamp": timestamp,
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


__all__ = ["AudioLoop", "AudioLoopState"]
