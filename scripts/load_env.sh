#!/usr/bin/env bash
# Usage: source scripts/load_env.sh

ENV_FILE="$(dirname "$BASH_SOURCE")/../.env"
if [ -f "$ENV_FILE" ]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "[load_env] .env not found; copy from .env.example" >&2
fi
