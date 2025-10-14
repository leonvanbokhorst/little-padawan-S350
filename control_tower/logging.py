"""Logging configuration utilities for Control Tower."""

from __future__ import annotations

import logging
import os
from typing import Optional


DEFAULT_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: Optional[str] = None, json_logs: bool = False) -> None:
    level_name = (level or os.environ.get("CONTROL_TOWER_LOG_LEVEL") or "INFO").upper()
    log_level = getattr(logging, level_name, logging.INFO)

    if json_logs:
        try:
            import pythonjsonlogger.jsonlogger as jsonlogger  # type: ignore
        except ImportError:
            logging.basicConfig(level=log_level, format=DEFAULT_FORMAT)
            logging.getLogger(__name__).warning(
                "python-json-logger not installed; falling back to text logs"
            )
            return

        handler = logging.StreamHandler()
        handler.setFormatter(jsonlogger.JsonFormatter())
        root = logging.getLogger()
        root.setLevel(log_level)
        root.handlers.clear()
        root.addHandler(handler)
    else:
        logging.basicConfig(level=log_level, format=DEFAULT_FORMAT)
