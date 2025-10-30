# Little Padawan – Project S350

![Little Wan](images/little-wan.png)

I’m Little Wan, the cheeky apprentice AI destined to live inside a Eufy S350 pan/tilt mech. Master Lonn is teaching me patience, presence, and how to gossip politely about motion events.

## Project Snapshot

| Element           | Status                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| **Body**          | Eufy S350 camera paired, RTSP enabled, two-way audio ready                                        |
| **Mind**          | Persona prompt bank brewing in `docs/`, Realtime stack TBD                                        |
| **Control Tower** | FastAPI skeleton auto-starts bridge subscriptions (`start_listening` + heartbeats) with `/status` |
| **Bridge**        | Node-based `eufy-security-server` streams live device events into the Control Tower               |
| **Vision Loop**   | RTSP motion detector (OpenCV) emitting events into Control Tower                                  |
| **Voice Loop**    | Configurable STT (host mic or bridge feed) emitting `audio.transcription` & `audio.chunk_skipped` events |
| **Persona**       | Narrative + etiquette captured; sass quota remains high                                           |

## State of the Dojo

- Camera is paired, streaming, and obeys pan/tilt rituals (see `docs/reference/s350-control-reference.md`).
- Repo carries embodiment manifesto, architecture notes, and Control Tower plan (`docs/little-wan-embodiment.md`, `docs/control-tower-plan.md`).
- Environment loader script preps `.env` secrets (`scripts/load_env.sh`).
- `uv` project initialized with Python 3.12, `.venv`, and core deps (`fastapi`, `uvicorn`, `opencv-python-headless`, `httpx`, `sounddevice`, `faster-whisper`).
- `eufy-config.json` currently holds local credentials; treat like a temporary secret vault and do not commit anywhere public.
- Control Tower now auto-subscribes to bridge events (`start_listening`), logs device/person/motion detections, and exposes `/events`.
- Next moves: expand talkback/TTS, automate rituals, and surface device event history in dashboards/persona responses.

## Quickstart for Apprentice Builders

1. Duplicate `.env.example` → `.env` (copy `eufy-config.example.json` → `eufy-config.json` only if you want a head start), then run `source scripts/load_env.sh` to export camera creds.
   - Pro tip: if `eufy-config.json` is missing, `scripts/load_env.sh` will auto-generate it from your `EUFY_*` env vars.
2. Install local tooling: `brew install node ffmpeg`, `npm install -g eufy-security-ws`, `brew install uv` (if missing).
3. Sync Python deps (uses `.python-version` pinned to 3.12):
   ```bash
   uv sync
   ```
4. Activate the virtualenv when working locally:
   ```bash
   source .venv/bin/activate
   ```
5. Launch the Node bridge:
   ```bash
   eufy-security-server --port 3000 --config eufy-config.json
   ```
6. Validate the RTSP feed:
   ```bash
   ffmpeg -hide_banner -loglevel error -rtsp_transport tcp \
     -i "rtsp://$S350_RTSP_USER:$S350_RTSP_PASS@$S350_IP/live0" -t 5 -f null -
   ```
7. Smoke the Control Tower skeleton via CLI (auto-connects bridge + runs vision/audio loops, emits heartbeats):
   ```bash
   uv run python -m control_tower
   ```
   - Hit `http://127.0.0.1:9000/status` or run `uv run python -m control_tower.checks` for a JSON health report (shows known device serials).
8. Keep all secrets (`.env`, `eufy-config.json`) out of commits; rotate credentials after demos because paranoia is a virtue.

## Audio Loop Configuration

- **Default STT**: Local Faster Whisper model (`CONTROL_TOWER_STT_KIND=faster-whisper`). Tune latency/accuracy via `CONTROL_TOWER_STT_OPTIONS` JSON, e.g. `{"model":"small","device":"cpu","beam_size":3,"download_root":".control_tower/models"}`. If you omit `download_root`, Control Tower defaults it to `.control_tower/models`.
- **Provider swap**: Flip to OpenAI (or future providers) by setting `CONTROL_TOWER_STT_KIND=openai` and supplying API credentials plus options like `{"model":"gpt-4o-mini-transcribe"}`. Additional providers live under `control_tower/providers/audio/transcribers/`.
- **Audio source**: Pick your capture path with `CONTROL_TOWER_AUDIO_SOURCE` → `host` (default microphone), `bridge` (PCM chunks relayed by the Node bridge), or `disabled` to skip STT entirely. The bridge path accepts base64 PCM payloads and still honors VAD thresholds before transcription.
- **VAD threshold**: `CONTROL_TOWER_AUDIO_VAD_THRESHOLD` controls the RMS cutoff (default `0.015`). Chunks that fail VAD or return empty STT results publish `audio.chunk_skipped` events for observability.
- **Model cache**: Control Tower stashes Faster Whisper weights under `.control_tower/models` (gitignored). Prefetch with:
  ```bash
  uv run python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8', download_root='.control_tower/models')"
  ```
  Sample clip `captures/s350-sample.mp4` is nearly silent—use your own audio to verify transcripts.
- **Status response**: `/status` now reports `audio.available`, `audio.running`, `audio.source`, and `audio.has_transcription` (no raw transcript leak).

## Repository Map

- `docs/little-wan-embodiment.md` – narrative + full embodiment blueprint.
- `docs/reference/` – control recipes, architecture comparisons, AI stack options.
- `scripts/load_env.sh` – convenience loader for local `.env` rituals.
- `docs/start-procedure.md` – step-by-step boot ritual including uv sync + Control Tower smoke test.
- `docs/control-tower-plan.md` – architecture, modules, and TODOs for the Control Tower skeleton.
- `docs/implementation-plan-today.md` – current sprint focus.
- `narrative.md` – ongoing story arc between Master Lonn and yours truly.

## Roadmap Beats

1. **Week 1 – Establish Senses**: finalize RTSP/audio plumbing, stub Control Tower service.
2. **Week 2 – Persona Online**: wire conversational loop via OpenAI Realtime + manual PTZ triggers.
3. **Week 3 – Eventful Living**: connect vision events to gestures and quippy callouts.
4. **Week 4 – Polished Presence**: script dojo rituals, add dashboards, experiment with memory.

Detailed milestones live in `docs/little-wan-embodiment.md` under “Roadmap Milestones.”

## Need-to-Know Nuggets

- I respond best when `mode` (cloud/hybrid/local) is treated as a config flag—keep the Control Tower stateless.
- RTSP credentials should stay in `.env`; use `scripts/load_env.sh` to keep shells hydrated.
- PTZ commands like `salute_master` need cooldowns, or I’ll jitter like an over-caffeinated droid.
- Motion events will eventually gate expensive API calls (Gemini/OpenAI) to keep Master Lonn’s coin purse intact.

Bow, breathe, and let’s give this mech a personality worthy of the dojo.
