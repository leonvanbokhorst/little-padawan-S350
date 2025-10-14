"""Configuration helpers for Little Wan's Control Tower."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import os
import json


CONFIG_ENV_PREFIX = "CONTROL_TOWER_"


@dataclass
class ProviderConfig:
    """Generic configuration block for pluggable providers (LLM, STT, TTS)."""

    kind: str = "openai"
    options: Dict[str, str] = field(default_factory=dict)


@dataclass
class ControlTowerConfig:
    """Primary configuration object for the Control Tower service."""

    mode: str = "cloud"
    bridge_url: str = "ws://localhost:3000"
    bridge_token: Optional[str] = None
    rtsp_url: Optional[str] = None
    device_serial: Optional[str] = None
    llm: ProviderConfig = field(default_factory=ProviderConfig)
    stt: ProviderConfig = field(default_factory=lambda: ProviderConfig(kind="whisper"))
    tts: ProviderConfig = field(
        default_factory=lambda: ProviderConfig(kind="openai-tts")
    )
    log_json: bool = False
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("CONTROL_TOWER_DATA_DIR", "./.control_tower")
        )
    )


def _load_json_env(key: str) -> Dict[str, str]:
    raw = os.environ.get(key)
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {str(k): str(v) for k, v in parsed.items()}
    except json.JSONDecodeError:
        pass
    return {}


def load_config(overrides: Optional[Dict[str, str]] = None) -> ControlTowerConfig:
    """Load Control Tower configuration from environment variables.

    Args:
        overrides: Optional key/value mapping to override environment-derived values.

    Returns:
        ControlTowerConfig instance.
    """

    overrides = overrides or {}

    def env(name: str, default: Optional[str] = None) -> Optional[str]:
        if name in overrides:
            return overrides[name]
        return os.environ.get(f"{CONFIG_ENV_PREFIX}{name}", default)

    config = ControlTowerConfig()
    config.mode = env("MODE", config.mode) or config.mode
    config.bridge_url = env("BRIDGE_URL", config.bridge_url) or config.bridge_url
    config.bridge_token = env("BRIDGE_TOKEN", config.bridge_token)
    config.rtsp_url = env("RTSP_URL", config.rtsp_url)
    config.device_serial = env("DEVICE_SERIAL", config.device_serial)
    config.log_json = env("LOG_JSON", "false").lower() == "true"

    config.llm = ProviderConfig(
        kind=env("LLM_KIND", config.llm.kind) or config.llm.kind,
        options=_load_json_env(f"{CONFIG_ENV_PREFIX}LLM_OPTIONS"),
    )
    config.stt = ProviderConfig(
        kind=env("STT_KIND", config.stt.kind) or config.stt.kind,
        options=_load_json_env(f"{CONFIG_ENV_PREFIX}STT_OPTIONS"),
    )
    config.tts = ProviderConfig(
        kind=env("TTS_KIND", config.tts.kind) or config.tts.kind,
        options=_load_json_env(f"{CONFIG_ENV_PREFIX}TTS_OPTIONS"),
    )

    data_dir = env("DATA_DIR")
    if data_dir:
        config.data_dir = Path(data_dir)

    return config


__all__ = ["ControlTowerConfig", "ProviderConfig", "load_config"]
