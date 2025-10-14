"""Health checks for Little Wan Control Tower."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

import httpx


async def check_status(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def main() -> None:
    base_url = os.environ.get(
        "CONTROL_TOWER_STATUS_URL", "http://127.0.0.1:9000/status"
    )
    try:
        result = asyncio.run(check_status(base_url))
    except Exception as exc:  # pragma: no cover
        print(f"Health check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
