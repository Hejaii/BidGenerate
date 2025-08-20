from __future__ import annotations

"""Utility helpers for unified logging configuration."""

import logging
from pathlib import Path


def get_logger(name: str, workdir: Path) -> logging.Logger:
    """Return a logger that writes to ``workdir/logs`` and stdout.

    Parameters
    ----------
    name:
        Logger name.
    workdir:
        Base working directory. Log file will be created under
        ``workdir / "logs" / "build.log"``.
    """
    logs_dir = workdir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "build.log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
