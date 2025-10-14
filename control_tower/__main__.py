"""CLI entry point for running the Control Tower."""

from __future__ import annotations

import uvicorn

from .app import create_app


def main() -> None:
    uvicorn.run(create_app, factory=True, host="127.0.0.1", port=9000)


if __name__ == "__main__":
    main()
