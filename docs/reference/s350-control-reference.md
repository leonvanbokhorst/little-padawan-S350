# S350 Control Reference (Little Wan Edition)

Curated notes from earlier research so Little Wan can steer, see, and speak through the Eufy S350 using the `eufy-security-client` ecosystem.

## Core Stack

- **Primary bridge:** `eufy-security-client` (Node/TypeScript) for device discovery, P2P livestream, talkback, RTSP toggling, and PTZ commands.
- **Python integration:** Use `eufy-security-ws` to expose a WebSocket API, then drive it from Python (`websockets` + asyncio) while keeping Node as the protocol brain.
- **Control loop:**
  - Python `Control Tower` connects to WebSocket → sends JSON commands like `device.pan_and_tilt`, `device.start_livestream`, `device.start_talkback`.
  - RTSP stream (`rtsp://<user>:<pass>@<ip>:8554/live0`) enabled via `device.set_property` (`rtspStream: true`) for OpenCV/ffmpeg ingest.

## Capability Checklist

| Capability              | How                                                                                           | Notes                                                                          |
| ----------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Device discovery**    | `client.getDevice(serial)` after `devices` event                                              | Need trusted device dir for refresh tokens (`persistentDir`).                  |
| **Pan / Tilt**          | `device.pan_and_tilt(direction)` where 0=up,1=down,2=left,3=right                             | Add sleep cooldowns to avoid jitter.                                           |
| **Presets / gestures**  | Build in Python: sequence of `pan_and_tilt` with delays                                       | e.g. `salute_master`, `zen_mode`.                                              |
| **Livestream (P2P)**    | `device.start_livestream` / `device.stop_livestream` events deliver raw H.264 + audio buffers | Save or pipe into ffmpeg for realtime processing.                              |
| **RTSP enable**         | `device.set_property` (`rtspStream: true`)                                                    | Once enabled, stream stays available even if Node bridge restarts.             |
| **Talkback start/stop** | `device.start_talkback` / `device.stop_talkback`                                              | Required before sending audio packets.                                         |
| **Send audio**          | `device.talkback_audio_data` with AAC_LC mono 16 kHz 16 kbps chunks                           | Use `ffmpeg -re -i input -ac 1 -ar 16000 -b:a 16k -acodec aac -f adts pipe:1`. |
| **Listen to mic**       | Start livestream and use `livestream audio data` events                                       | Buffers contain AAC; append to file or decode on the fly.                      |
| **Status / props**      | `device.get_properties`                                                                       | Use to confirm talkback/stream state, night mode, etc.                         |

## Minimal Python Control Flow

1. Start Node bridge:
   ```bash
   eufy-security-ws --port 3000 --config config.json
   ```
2. Python client connects (`ws://localhost:3000`), listens for `result`/`event` messages, sends commands with incremental `messageId`.
3. Wrap helpers:
   - `EufyCamera.pan(direction)`
   - `EufyCamera.start_stream(mode="rtsp"|"p2p")`
   - `EufyCamera.speak(audio_path)` → convert with ffmpeg streaming + send via talkback.
4. Integrate into Control Tower tasks (vision loop consumes RTSP, audio loop pipes to STT, etc.).

## Implementation Tips

- Store credentials in `config.json`; keep `persistentDir` on disk so we don’t need to re-login after restarts.
- When reading livestream video data, expect raw H.264—requires ffmpeg demux before OpenCV can consume. Using RTSP is easier for computer-vision tasks.
- Add exponential backoff/retry around connect/start commands; the Eufy cloud occasionally rate-limits.
- For talkback, chunk size ~4KB with `await asyncio.sleep(0.05)` between sends keeps audio smooth.
- The S350 mic + speaker work over the same talkback session—no external hardware needed for baseline embodiment.

## Reference Snippets

- **Pan sequence: **
  ```python
  await camera.pan_and_tilt(0); await asyncio.sleep(1)
  await camera.pan_and_tilt(3); await asyncio.sleep(1)
  ```
- **RTSP enable command:**
  ```json
  {
    "command": "device.set_property",
    "serialNumber": "S350_SERIAL",
    "name": "rtspStream",
    "value": true
  }
  ```
- **FFmpeg talkback pipeline:**
  ```bash
  ffmpeg -re -i speak.wav -acodec aac -ac 1 -ar 16000 -b:a 16k -f adts pipe:1
  ```

## Onboarding Ritual (MacBook + S350)

1. **Pair the mech**

   - Add the S350 in the Eufy Security mobile app, confirm you can see live video + two-way audio.
   - Update firmware if prompted (Settings → About Device → Firmware).
   - Note the camera’s serial number from the About screen.

2. **Enable RTSP / NAS**

   - App path: `Settings → General → Storage → NAS (RTSP)`.
   - Toggle on, set a stream username/password, save the generated URL (`rtsp://user:pass@CAM-IP:8554/live0`).
   - If the toggle is missing, finish pairing, force-close/reopen the app, or update firmware. As last resort, enable it later via the WebSocket command in the snippets section.

3. **Prep the Mac dojo brain**

   ```bash
   brew update
   brew install node ffmpeg
   npm install -g eufy-security-ws
   ```

4. **Create config** (repo root `eufy-config.json`)

   ```json
   {
     "username": "your-eufy-email@example.com",
     "password": "your-eufy-password",
     "country": "NL",
     "trustedDeviceName": "LittleWanMac",
     "persistentDir": "./.eufy-data"
   }
   ```

   Adjust country code to your region (e.g. "US", "DE"). Use a dedicated Eufy account if possible. Keep file permissions tight (`chmod 600 eufy-config.json`).

5. **Start the bridge**

   ```bash
   /Users/leonvanbokhorst/.npm-global/bin/eufy-security-server --port 3000 --config /Users/leonvanbokhorst/repos/little-padawan-S350/eufy-config.json
   ```

   - If the binary isn’t in PATH, locate it via `npm config get prefix` and point directly as above.
   - Watch logs for successful login. Error `26006` means wrong credentials/region or 2FA still pending.

6. **Verify stream**
   ```bash
   ffmpeg -i rtsp://user:pass@CAM-IP:8554/live0 -f null -
   ```
   - Camera mic/speaker work through the same talkback channel; no extra hardware required.
   - Keep the bridge running in its own terminal tab while developing the Python Control Tower.

## Next Steps for Little Wan

- Wrap WebSocket calls in a Python `VirtualHumanController` (see research) and expose high-level actions: `look(direction)`, `speak(text)`, `start_watch()`, etc.
- Integrate into Control Tower event loop with the persona engine; tie camera gestures to dialogue states.
- Optionally extend Node bridge with custom endpoints if we need aggregated status or queueing.
