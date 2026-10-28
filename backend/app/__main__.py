"""Supported local release launcher: python -m app [--port 8000]."""

import argparse
from pathlib import Path

import uvicorn

from app.main import create_app


def main():
    parser = argparse.ArgumentParser(
        description="Run CyrNava locally with the built frontend."
    )
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        application = create_app(
            frontend_path=Path(__file__).resolve().parents[2] / "frontend/dist"
        )
    except RuntimeError as error:
        parser.error(str(error))
    uvicorn.run(application, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
