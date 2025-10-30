"""Configuration helpers for Little Wan's Control Tower."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

import os
import json
import logging


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
    audio_source: str = "host"
    audio_vad_threshold: float = 0.015
    llm: ProviderConfig = field(default_factory=ProviderConfig)
    stt: ProviderConfig = field(
        default_factory=lambda: ProviderConfig(kind="faster-whisper")
    )
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
    config.audio_source = (
        env("AUDIO_SOURCE", config.audio_source) or config.audio_source
    ).lower()
    vad_threshold = env("AUDIO_VAD_THRESHOLD")
    if vad_threshold is not None:
        try:
            config.audio_vad_threshold = float(vad_threshold)
        except ValueError:
            LOGGER = logging.getLogger(__name__)
            LOGGER.warning(
                "Invalid CONTROL_TOWER_AUDIO_VAD_THRESHOLD '%s'; using default %.3f",
                vad_threshold,
                config.audio_vad_threshold,
            )
    config.log_json = env("LOG_JSON", "false").lower() == "true"

    config.llm = ProviderConfig(
        kind=env("LLM_KIND", config.llm.kind) or config.llm.kind,
        options=_load_json_env(f"{CONFIG_ENV_PREFIX}LLM_OPTIONS"),
    )
    stt_options = _load_json_env(f"{CONFIG_ENV_PREFIX}STT_OPTIONS")
    if (
        "download_root" not in stt_options
        or stt_options["download_root"] is None
        or (isinstance(stt_options["download_root"], str) and stt_options["download_root"].strip() == "")
    ):
        stt_options["download_root"] = ".control_tower/models"
    config.stt = ProviderConfig(
        kind=env("STT_KIND", config.stt.kind) or config.stt.kind,
        options=stt_options,
    )
    config.tts = ProviderConfig(
        kind=env("TTS_KIND", config.tts.kind) or config.tts.kind,
        options=_load_json_env(f"{CONFIG_ENV_PREFIX}TTS_OPTIONS"),
    )

    data_dir = env("DATA_DIR")
    if data_dir:
        config.data_dir = Path(data_dir)

    if not config.bridge_url:
        raise ValueError("CONTROL_TOWER_BRIDGE_URL (bridge_url) must be set")
    if config.device_serial is None:
        LOGGER = logging.getLogger(__name__)  # lazy import
        LOGGER.warning(
            "CONTROL_TOWER_DEVICE_SERIAL not set; bridge commands will operate without a target device"
        )
    if config.rtsp_url is None:
        LOGGER = logging.getLogger(__name__)
        LOGGER.info("CONTROL_TOWER_RTSP_URL not set; vision loop will be disabled")

    return config


__all__ = ["ControlTowerConfig", "ProviderConfig", "load_config"]
