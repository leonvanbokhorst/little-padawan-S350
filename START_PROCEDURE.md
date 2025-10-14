# START_PROCEDURE — Little Wan Boot Ritual

Use this checklist when spinning Little Wan back online. Assume you are working from `/Users/leonvanbokhorst/repos/little-padawan-S350`.

## 0. Preflight

1. **Power & network**
   - Verify the Eufy S350 is powered and on the dojo Wi-Fi (green LED, reachable from router list).
2. **Secrets**
   - Confirm `.env` exists and includes `S350_RTSP_USER`, `S350_RTSP_PASS`, `S350_IP`, plus any API keys.
   - If you pulled fresh changes, run `git status` to ensure `.env` stays untracked.

## 1. Hydrate the Shell

```bash
source scripts/load_env.sh
```

- Quick sanity check:

```bash
/usr/bin/python3 - <<'PY'
import os
for key in ("S350_RTSP_USER", "S350_RTSP_PASS", "S350_IP"):
    print(f"{key} present? {bool(os.environ.get(key))}")
PY
```

Expect three `True` values. If not, fix `.env` before proceeding.

## 2. Wake the Bridge

Launch the Node PTZ/audio bridge:

```bash
/Users/leonvanbokhorst/.npm-global/bin/eufy-security-server \
  --port 3000 \
  --config /Users/leonvanbokhorst/repos/little-padawan-S350/eufy-config.json
```

- Keep this terminal running; it streams PTZ/talkback logs.
- If credentials expired, re-authenticate in the Eufy app and update `eufy-config.json`.

## 3. Verify the Camera Feed

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

## 4. (Future) Start Control Tower

Once the Python Control Tower exists:

```bash
uvicorn control_tower.app:app --reload
```

- Confirm it connects to `ws://localhost:3000` and subscribes to PTZ/vision events.
- Update this doc when the Control Tower gains a real entry point.

## 5. Shut Down Gracefully

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
