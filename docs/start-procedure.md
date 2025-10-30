# START_PROCEDURE — Little Wan Boot Ritual

Use this checklist when spinning Little Wan back online. Assume you are working from the project root.

## 0. Preflight

1. **Power & network**
   - Verify the Eufy S350 is powered and on the dojo Wi-Fi (green LED, reachable from router list).
2. **Secrets**
   - Confirm `.env` exists and includes the S350 RTSP trio (`S350_RTSP_USER`, `S350_RTSP_PASS`, `S350_IP`).
   - Verify Control Tower settings such as `CONTROL_TOWER_BRIDGE_URL`, `CONTROL_TOWER_AUDIO_SOURCE` (`host`, `bridge`, or `disabled`), `CONTROL_TOWER_AUDIO_VAD_THRESHOLD`, and any provider overrides in `CONTROL_TOWER_STT_KIND` / `_OPTIONS`.
   - Ensure `eufy-config.json` is present (copy from `eufy-config.example.json` if missing) and populated with your bridge credentials; keep it out of version control.
   - If you pulled fresh changes, run `git status` to ensure `.env` stays untracked.

## 1. Hydrate the Shell

```bash
source scripts/load_env.sh
```

- This will also auto-generate `eufy-config.json` when it’s missing and the necessary `EUFY_*` vars are present.

- Quick sanity check:

```bash
/usr/bin/python3 - <<'PY'
import os
for key in (
    "S350_RTSP_USER",
    "S350_RTSP_PASS",
    "S350_IP",
    "CONTROL_TOWER_BRIDGE_URL",
    "CONTROL_TOWER_AUDIO_SOURCE",
):
    print(f"{key} present? {bool(os.environ.get(key))}")
PY
```

Expect `True` across the board (audio source can be blank only when using defaults). If not, fix `.env` before proceeding.

## 2. Sync Python Environment (first run or dependency changes)

```bash
uv sync
```

- Creates/updates `.venv` using Python 3.12 pinned via `.python-version`.

Activate the environment when working locally:

```bash
source .venv/bin/activate
```

## 3. Wake the Bridge

Launch the Node PTZ/audio bridge:

```bash
eufy-security-server \
  --port 3000 \
  --config eufy-config.json
```

- Keep this terminal running; it streams PTZ/talkback logs.
- If credentials expired, re-authenticate in the Eufy app and update `eufy-config.json`.

## 4. Verify the Camera Feed

In a second shell (source the env again):

```bash
ffprobe -hide_banner -rtsp_transport tcp \
  -i "rtsp://$S350_RTSP_USER:$S350_RTSP_PASS@$S350_IP/live0"
```

- Expect `1920x1080` video + `aac` audio. Any `Connection refused` errors usually mean IP changed or RTSP toggled off.

Optional live peek:

```bash
ffplay -rtsp_transport tcp "rtsp://$S350_RTSP_USER:$S350_RTSP_PASS@$S350_IP/live0"
```

## 5. Start Control Tower Skeleton

From an activated `.venv` shell:

```bash
uv run python -m control_tower
```

- Visit `http://127.0.0.1:9000/status` or run `uv run python -m control_tower.checks` for a quick health report. The `audio` block should show the configured source and whether STT is running.
- Leave this running while testing downstream loops.

## 6. Shut Down Gracefully

When finished:

1. `Ctrl+C` the Control Tower.
2. `Ctrl+C` the Node bridge (let it close sessions cleanly).
3. Consider parking the camera via preset (future scripted command) or closing the Eufy app stream.

## Quick Troubleshooting

- **RTSP connection refused** → Ping the camera (`ping $S350_IP`), confirm RTSP toggle in the Eufy app, or redo `.env` credentials.
- **Bridge login errors (26006)** → Wrong region/password/2FA; fix credentials and delete `.eufy-data` cache before retrying.
- **Audio stutter** → Restart bridge, ensure only one talkback client is running, and keep `ffmpeg` jobs lightweight.
- **Forgot a step?** → Re-read `README.md` for architecture context or `docs/reference/s350-control-reference.md` for command specifics.

Bow, breathe, and let the mech awaken with style.
