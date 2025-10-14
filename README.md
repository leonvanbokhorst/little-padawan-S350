# Little Padawan – Project S350

![Little Wan](images/little-wan.png)

I’m Little Wan, the cheeky apprentice AI destined to live inside a Eufy S350 pan/tilt mech. Master Lonn is teaching me patience, presence, and how to gossip politely about motion events.

## Project Snapshot

| Element           | Status                                                                                     |
| ----------------- | ------------------------------------------------------------------------------------------ |
| **Body**          | Eufy S350 camera paired, RTSP enabled, two-way audio ready                                 |
| **Mind**          | Persona prompt bank brewing in `docs/`, Realtime stack TBD                                 |
| **Control Tower** | FastAPI skeleton live via CLI (`python -m control_tower`), logging + scheduler + `/status` |
| **Bridge**        | Node-based `eufy-security-server` handles PTZ, talkback, property toggles                  |
| **Vision Loop**   | RTSP motion detector (OpenCV) emitting events into Control Tower                           |
| **Voice Loop**    | Planned: Realtime TTS + talkback streaming with AAC glue                                   |
| **Persona**       | Narrative + etiquette captured; sass quota remains high                                    |

## State of the Dojo

- Camera is paired, streaming, and obeys pan/tilt rituals (see `docs/reference/s350-control-reference.md`).
- Repo carries embodiment manifesto, architecture notes, and Control Tower plan (`docs/little-wan-embodiment.md`, `docs/control-tower-plan.md`).
- Environment loader script preps `.env` secrets (`scripts/load_env.sh`).
- `uv` project initialized with Python 3.12, `.venv`, and core deps (`fastapi`, `uvicorn`, `opencv-python-headless`, `httpx`).
- `eufy-config.json` currently holds local credentials; treat like a temporary secret vault and do not commit anywhere public.
- Control Tower skeleton now connects to bridge, exposes `/events`, emits motion + heartbeat events, and ships with CLI/health checks.
- Next moves: hook to live bridge events, implement audio loops, and automate rituals.

## Quickstart for Apprentice Builders

1. Duplicate `.env.example` → `.env`, then run `source scripts/load_env.sh` to export camera creds.
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
   /Users/leonvanbokhorst/.npm-global/bin/eufy-security-server --port 3000 --config /Users/leonvanbokhorst/repos/little-padawan-S350/eufy-config.json
   ```
6. Validate the RTSP feed:
   ```bash
   ffmpeg -hide_banner -loglevel error -rtsp_transport tcp \
     -i "rtsp://$S350_RTSP_USER:$S350_RTSP_PASS@$S350_IP/live0" -t 5 -f null -
   ```
7. Smoke the Control Tower skeleton via CLI:
   ```bash
   uv run python -m control_tower
   ```
   - Hit `http://127.0.0.1:9000/status` or run `uv run python -m control_tower.checks` for a JSON health report.
8. Keep all secrets (`.env`, `eufy-config.json`) out of commits; rotate credentials after demos because paranoia is a virtue.

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
