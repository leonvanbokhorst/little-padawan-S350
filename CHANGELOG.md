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
