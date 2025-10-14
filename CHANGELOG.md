# Changelog

All notable sass and mech upgrades will be documented here.

## 2025-10-14

- Bootstrapped Control Tower CLI (`python -m control_tower`) with logging config, scheduler heartbeats, and `/status` health endpoint.
- Wired OpenCV-based RTSP motion detection into the event bus; vision loop now emits `vision.motion` events.
- Upgraded BridgeClient with normalized events and helper commands; ready for live `eufy-security-server` integration.
- Added health check CLI (`python -m control_tower.checks`) for quick status probes.
- Updated startup ritual docs (`docs/start-procedure.md`) and README snapshots to match the new workflow.
