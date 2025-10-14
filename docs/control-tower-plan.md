# Control Tower Skeleton Plan (Little Wan)

## 1. Goals for the Skeleton

- Provide a central Python service coordinating vision, audio, and ritual loops.
- Expose clear interfaces for inbound events (Eufy bridge, vision loop) and outbound actions (PTZ gestures, speech).
- Remain mode-agnostic (`cloud`, `hybrid`, `local`) with configuration-driven providers.
- Deliver health insight (status endpoint, heartbeat logs) before layering complex features.

## 2. High-Level Architecture

```
                 ┌─────────────────────────┐
                 │      Eufy Bridge        │
                 │ (eufy-security-server)  │
                 └────────────┬────────────┘
                              │ WebSocket events / commands
                              ▼
┌───────────────────────────────────────────────────────────┐
│                   Control Tower (Python)                  │
│                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐ │
│  │Config Loader │   │ Event Bus    │   │ Provider Adapters│
│  └──────────────┘   └──────────────┘   └────────────────┘ │
│        │                 │                    │           │
│   (mode detection)  (pub/sub)          (vision, audio, etc)│
│                                                           │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐ │
│  │ FastAPI App  │   │ Scheduler    │   │ Logging/Telemetry││
│  └──────────────┘   └──────────────┘   └────────────────┘ │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │    Vision & Audio Loops  │
                 │  (async tasks/services)  │
                 └─────────────────────────┘
```

## 3. Module Breakdown

### 3.1 `control_tower/__init__.py`

- Top-level package exports: `create_app(config)`, `startup()`, `shutdown()`.
- Handles version metadata.

### 3.2 `control_tower/config.py`

- `ControlTowerConfig` dataclass with fields:
  - `mode` (`cloud|hybrid|local`)
  - `bridge_url`, `bridge_token` (optional)
  - `rtsp_url`
  - provider settings (`llm`, `stt`, `tts`)
  - logging preferences.
- `load_config()` reading env vars + `configs/*.yml` if present.

### 3.3 `control_tower/app.py`

- FastAPI application factory.
- Routes:
  - `GET /status` – return uptime, mode, last heartbeat, connected providers.
  - `POST /events` – accept external events (e.g., test triggers, manual rituals).
  - (Future) WebSocket for dashboards.
- Startup/shutdown handlers to launch background tasks.

### 3.4 `control_tower/events.py`

- Lightweight pub/sub bus (asyncio Queue-based) supporting topics.
- Event model structure: `id`, `type`, `payload`, `source`, `timestamp`.
- Convenience emit/listen helpers.

### 3.5 `control_tower/providers/`

#### `bridge.py`

- Async client for `eufy-security-server` WebSocket.
- Methods: `connect()`, `send_command(...)`, `subscribe_events(callback)`.
- Includes cooldown + retry logic (exponential backoff).

#### `vision.py`

- Placeholder for RTSP consumer (OpenCV) hooking into event bus.
- Supports `start()`, `stop()`, and `on_frame` callbacks.

#### `audio.py`

- Stub interface for STT/TTS providers based on config.
- Methods: `transcribe_stream()`, `speak(text, voice)`.

#### `persona.py`

- Holds persona prompts, memory hooks, fallback scripts.

### 3.6 `control_tower/scheduler.py`

- Wraps `asyncio` tasks with registration decorators (`@scheduled(interval=...)`).
- Predefine heartbeats: `report_status`, `flush_metrics`.

### 3.7 `control_tower/logging.py`

- Configure structured logging (JSON optional).
- Provide helper for event audit trails.

### 3.8 CLI Entrypoint (WIP)

- `uv run uvicorn control_tower.app:create_app --factory` → start FastAPI service.
- TODO: `python -m control_tower` convenience launcher.
- TODO: `python -m control_tower.checks` health diagnostics.

## 4. Startup Sequence

1. Load configuration (env + file).
2. Initialize logging + metrics.
3. Connect to Eufy bridge (WebSocket) and register event handlers.
4. Launch FastAPI app (Uvicorn) with background tasks for event processing.
5. Kick off scheduler heartbeats.
6. Start vision/audio loops (optional for day one; stub with logs).

## 5. Event Flow Example

1. **Bridge event**: PTZ status update arrives via WebSocket.
2. **Event bus**: `events.emit("bridge.ptz", payload)`.
3. **Handler**: Control Tower routine listens, updates state, optionally triggers persona response.
4. **Persona reaction**: triggers audio provider → talkback command.
5. **Logs** capture entire chain for debugging/ritual stories.

## 6. Immediate TODOs for Implementation

- [x] Set up Python package structure (`control_tower/` with `__init__.py`).
- [x] Implement `config.py` + baseline environment loading.
- [x] Create FastAPI app with `/status` route and server startup script.
- [x] Draft event bus + stub providers that log calls.
- [x] Add CLI entry to start service (`uv run uvicorn control_tower.app:create_app --factory`).
- [x] Write placeholder tests or smoke checks (import, config load).
- [ ] Update `START_PROCEDURE.md` with Control Tower launch command once implemented.

Sass responsibly, log obsessively, and keep the dojo calm.
