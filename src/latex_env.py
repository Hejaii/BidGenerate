from __future__ import annotations

import logging
import shutil
import subprocess

def ensure_latex_env(logger: logging.Logger) -> None:
    """Verify XeLaTeX and Noto CJK fonts are available.

    Raises
    ------
    RuntimeError
        If XeLaTeX or Noto CJK fonts are missing.
    """
    if shutil.which("xelatex") is None:
        raise RuntimeError(
            "XeLaTeX not found. Please install TeX Live with xelatex support."
        )

    try:
        result = subprocess.run(
            ["fc-list", "Noto Sans CJK"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "fontconfig utility 'fc-list' is required to verify fonts. "
            "Please install fonts-noto-cjk and fontconfig."
        ) from exc

    if not result.stdout.strip():
        raise RuntimeError(
            "Noto Sans CJK fonts not found. Please install fonts-noto-cjk."
        )

    logger.info("XeLaTeX and Noto fonts detected")
