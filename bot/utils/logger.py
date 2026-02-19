"""Loguru setup: file rotation, console level. Critical errors can be sent to admin from main."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: str = "logs") -> None:
    """
    Configure loguru: file per day, rotation 5 MB, console INFO, file DEBUG.
    """
    logger.remove()
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    file_sink = log_path / "bot_{time:YYYY-MM-DD}.log"
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
    )
    logger.add(
        str(file_sink),
        level="DEBUG",
        rotation="5 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
    )


def get_logger(name: str):
    """Return a logger with the given name (e.g. module __name__)."""
    return logger.bind(name=name)
