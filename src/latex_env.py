"""Helpers for preparing a minimal LaTeX environment.

This module makes a best effort to ensure that XeLaTeX and common
Chinese fonts are available.  It installs packages only when the
corresponding binaries or fonts are missing.  The function is intentionally
idempotent so it can be called before each compilation without a large
penalty.
"""
from __future__ import annotations

import logging
import shutil
import subprocess


def _run(cmd: list[str], logger: logging.Logger) -> None:
    """Run a command and log failures without raising."""
    try:
        logger.debug("running %s", " ".join(cmd))
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as exc:  # pragma: no cover - best effort only
        logger.warning("command failed: %s", exc)


def ensure_latex_env(logger: logging.Logger | None = None) -> None:
    """Ensure XeLaTeX and basic Chinese fonts exist.

    The function attempts to install TeX Live and Noto CJK fonts when they are
    missing.  It never raises on failure; compilation will surface any real
    errors later.
    """
    logger = logger or logging.getLogger(__name__)

    if shutil.which("xelatex") is None:
        logger.info("xelatex missing – installing TeX Live")
        _run(["apt-get", "update"], logger)
        _run(
            [
                "apt-get",
                "install",
                "-y",
                "texlive-xetex",
                "texlive-fonts-recommended",
                "texlive-latex-extra",
                "texlive-lang-chinese",
            ],
            logger,
        )

    # check for Chinese fonts
    proc = subprocess.run(
        ["bash", "-lc", "fc-list :lang=zh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if not proc.stdout.strip():
        logger.info("Chinese fonts missing – installing Noto CJK")
        _run(["apt-get", "install", "-y", "fonts-noto-cjk"], logger)
