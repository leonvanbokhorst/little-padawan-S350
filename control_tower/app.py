"""FastAPI application factory for Little Wan's Control Tower."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI

from .config import ControlTowerConfig, load_config
from .events import EventBus, Event
from .logging import configure_logging
from .providers.bridge import BridgeClient
from .scheduler import Scheduler
from .vision import VisionLoop

LOGGER = logging.getLogger(__name__)


def create_app(config: ControlTowerConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    config = config or load_config()
    configure_logging(json_logs=config.log_json)

    app = FastAPI(title="Little Wan Control Tower", version="0.1.0")

    app.state.config = config
    app.state.started_at = datetime.utcnow()
    app.state.event_bus = EventBus()
    app.state.bridge_client = BridgeClient(config.bridge_url, config.bridge_token)
    app.state.scheduler = Scheduler()
    app.state.vision_loop = VisionLoop(
        app.state.event_bus,
        config.rtsp_url,
    )

    async def bridge_event_handler(payload: Dict[str, Any]) -> None:
        event_type = payload.get("type", "bridge.raw")
        event = Event(type=event_type, payload=payload, source="bridge")
        if event_type.startswith("bridge.event"):
            LOGGER.info("Bridge event %s", event_type)
        app.state.event_bus.publish(event)

    app.state.scheduler.register(
        "heartbeat",
        60.0,
        lambda: heartbeat_task(app),
    )

    @app.get("/status")
    async def status() -> Dict[str, Any]:
        return {
            "status": "ok",
            "mode": app.state.config.mode,
            "uptime_seconds": (
                datetime.utcnow() - app.state.started_at
            ).total_seconds(),
            "bridge_url": app.state.config.bridge_url,
            "devices": list(app.state.bridge_client.devices.keys()),
        }

    @app.on_event("startup")
    async def on_startup() -> None:
        LOGGER.info("Starting Control Tower in %s mode", app.state.config.mode)
        await app.state.bridge_client.connect(bridge_event_handler)
        await app.state.bridge_client.start_listening()
        if app.state.config.device_serial:
            LOGGER.info(
                "Ensuring metadata for device %s", app.state.config.device_serial
            )
            await app.state.bridge_client.ensure_station_metadata(
                app.state.config.device_serial
            )
        await app.state.vision_loop.start()
        await app.state.scheduler.start()

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        await app.state.scheduler.stop()
        await app.state.bridge_client.close()
        await app.state.vision_loop.stop()

    @app.post("/events")
    async def ingest_event(event: Dict[str, Any]) -> Dict[str, str]:
        app.state.event_bus.publish(
            Event(type=event.get("type", "manual"), payload=event, source="manual")
        )
        return {"received": event.get("type", "unknown")}

    return app


async def heartbeat_task(app: FastAPI) -> None:
    app.state.event_bus.publish(
        Event(
            type="system.heartbeat",
            payload={
                "uptime_seconds": (
                    datetime.utcnow() - app.state.started_at
                ).total_seconds()
            },
            source="scheduler",
        )
    )


__all__ = ["create_app"]
