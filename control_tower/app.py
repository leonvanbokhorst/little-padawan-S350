"""FastAPI application factory for Little Wan's Control Tower."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI

from .config import ControlTowerConfig, load_config
from .events import EventBus, Event
from .providers.bridge import BridgeClient
from .vision import VisionLoop


def create_app(config: ControlTowerConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    config = config or load_config()
    app = FastAPI(title="Little Wan Control Tower", version="0.1.0")

    app.state.config = config
    app.state.started_at = datetime.utcnow()
    app.state.event_bus = EventBus()
    app.state.bridge_client = BridgeClient(config.bridge_url, config.bridge_token)
    app.state.vision_loop = VisionLoop(
        app.state.event_bus,
        config.rtsp_url,
    )

    async def bridge_event_handler(payload: Dict[str, Any]) -> None:
        event = Event(
            type=payload.get("type", "bridge.raw"), payload=payload, source="bridge"
        )
        app.state.event_bus.publish(event)

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

    @app.on_event("startup")
    async def on_startup() -> None:
        await app.state.bridge_client.connect(bridge_event_handler)
        await app.state.vision_loop.start()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.bridge_client.close()
        await app.state.vision_loop.stop()

    @app.post("/events")
    async def ingest_event(event: Dict[str, Any]) -> Dict[str, str]:
        app.state.event_bus.publish(
            Event(type=event.get("type", "manual"), payload=event, source="manual")
        )
        return {"received": event.get("type", "unknown")}

    return app


__all__ = ["create_app"]
