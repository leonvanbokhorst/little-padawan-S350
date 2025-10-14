# Implementation Plan — Little Wan Sprint (Today)

## 1. Control Tower Skeleton

- Scaffold `control_tower/` Python package with configuration modes (`cloud`, `hybrid`, `local`).
- Stand up FastAPI app exposing `/status` and `/events` routes plus websocket connection to `eufy-security-server`.
- Add async scheduler hooks to support future rituals, heartbeats, and graceful shutdown logic.

## 2. Eufy Bridge Integration

- Implement Python adapter wrapping Node bridge commands (PTZ, talkback, RTSP toggles) with built-in cooldowns.
- Define preset gestures (`salute_master`, `zen_mode`, `scan_room`) and log every outbound command/response for tracing.
- Capture bridge metrics (latency, errors) for observability.

## 3. Vision Loop MVP

- Consume RTSP stream via OpenCV async generator; add fallback to recorded clips for testing.
- Implement motion detection and subscribe to Eufy “person detected” events where available.
- Emit structured events (`motion.start`, `motion.stop`, `person.detected`) into the Control Tower event bus with timestamps.

## 4. Persona & Audio Wiring

- Establish Realtime STT/TTS pipeline (local Faster Whisper baseline, swappable to OpenAI/Gemini) with persona prompt pulled from `narrative.md`.
- Route synthesized audio through bridge adapter talkback channel; enforce rate limiting and queue management.
- Maintain short-term memory buffer (recent transcripts, rituals triggered) to keep responses contextual and witty.

## 5. Diagnostics & Ritual Tools

- Create CLI entry `python -m control_tower.checks` to run RTSP, bridge, and API health probes.
- Extend `START_PROCEDURE.md` references inside code comments and add TODO hook for automated shutdown ritual.
- Log API usage metrics and outline budget guardrails for cloud services.

Bow, breathe, execute—report back to Master Lonn when each kata lands.
