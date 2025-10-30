#!/usr/bin/env bash
# Usage: source scripts/load_env.sh

ENV_FILE="$(dirname "$BASH_SOURCE")/../.env"
CONFIG_FILE="$(dirname "$BASH_SOURCE")/../eufy-config.json"

if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)

  if [ ! -f "$CONFIG_FILE" ]; then
    python3 - "$CONFIG_FILE" <<'PY'
import json
import os
import pathlib
import sys

config_path = pathlib.Path(sys.argv[1]).resolve()

required = ["EUFY_EMAIL", "EUFY_PASSWORD", "EUFY_COUNTRY"]
missing = [key for key in required if not os.environ.get(key)]
if missing:
    sys.stderr.write(
        "[load_env] skipping eufy-config.json auto-generation; missing env: "
        + ", ".join(missing)
        + "\n"
    )
    sys.exit(0)

config = {
    "username": os.environ.get("EUFY_EMAIL", ""),
    "password": os.environ.get("EUFY_PASSWORD", ""),
    "country": os.environ.get("EUFY_COUNTRY", ""),
    "trustedDeviceName": os.environ.get(
        "EUFY_TRUSTED_DEVICE_NAME", "LittleWanWorkstation"
    ),
    "persistentDir": os.environ.get("EUFY_PERSISTENT_DIR", "./.eufy-data"),
}

config_path.write_text(json.dumps(config, indent=2))

try:
    config_path.chmod(0o600)
except PermissionError:
    pass

try:
    pathlib.Path(config["persistentDir"]).mkdir(parents=True, exist_ok=True)
except Exception:
    pass

print("[load_env] generated eufy-config.json")
PY
  fi
else
  echo "[load_env] .env not found; copy from .env.example" >&2
fi
