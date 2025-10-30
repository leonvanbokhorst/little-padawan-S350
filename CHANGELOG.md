# Changelog

All notable sass and mech upgrades will be documented here.

## 2025-10-14

- Control Tower now auto-subscribes to the bridge (`start_listening`, `driver.connect`, `driver.poll_refresh`) and logs `bridge.event.*` detections.
- BridgeClient stores live device metadata/events, exposes known devices on `/status`, and powers rituals without manual scripts.
- Vision loop still streaming RTSP motion; next stop: fuse audio loops + persona reactions.
- Docs refreshed (`README.md`, `docs/start-procedure.md`) to reflect the hands-free bridge wiring.
- Event bus now schedules async listeners to avoid blocking; `/events` endpoint upgraded to a Pydantic model.
- Configuration fails fast when critical values are missing and warns when optional pieces (RTSP URL/device serial) are absent.
- Bridge internals refactored into `MessageNormalizer` / `DeviceRegistry` with capped event history for sane memory usage.

## 2025-10-14 — Audio Loop Awakens

- Faster Whisper STT loop wired into the Control Tower with pluggable providers and CPU INT8 defaults for the dojo Mac.
- New `.control_tower/models` cache path keeps whisper weights local (auto-seeded from config), plus host mic transcription smoke-tested.
- README/plan docs refreshed with audio config, env knobs, and model caching ritual guidance.

## 2025-10-30 — Audio Dojo Refactor

- Audio provider split into modular package: `audio/loop.py`, `stt_factory.py`, and `transcribers/` (Faster Whisper, OpenAI, debug).
- `AudioLoop` now respects `CONTROL_TOWER_AUDIO_SOURCE`, handles bridge-forwarded PCM, and surfaces sanitized status snapshots.
- VAD threshold config (`CONTROL_TOWER_AUDIO_VAD_THRESHOLD`) finally powers the loop; skipped chunks publish `audio.chunk_skipped` events.
- `/status` API exposes `audio.available`, `audio.running`, `audio.source`, and `audio.has_transcription` only—no transcript leaks.
- `.env.example`, README, and docs updated with new env knobs, provider guidance, and refreshed architecture notes.
