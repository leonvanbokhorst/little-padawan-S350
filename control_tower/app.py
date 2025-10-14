"""FastAPI application factory for Little Wan's Control Tower."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI

from .config import ControlTowerConfig, load_config


def create_app(config: ControlTowerConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    config = config or load_config()
    app = FastAPI(title="Little Wan Control Tower", version="0.1.0")

    app.state.config = config
    app.state.started_at = datetime.utcnow()

    @app.get("/status")
    async def status() -> Dict[str, Any]:
        return {
            "status": "ok",
            "mode": app.state.config.mode,
            "uptime_seconds": (
                datetime.utcnow() - app.state.started_at
            ).total_seconds(),
            "bridge_url": app.state.config.bridge_url,
        }

    @app.post("/events")
    async def ingest_event(event: Dict[str, Any]) -> Dict[str, str]:
        # TODO: Push into event bus once implemented.
        return {"received": event.get("type", "unknown")}

    return app


__all__ = ["create_app"]
