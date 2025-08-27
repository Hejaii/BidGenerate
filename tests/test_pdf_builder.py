import shutil
from pathlib import Path

import pytest

from src.logging_utils import get_logger
from src.pdf_builder import compile_pdf


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_compile_pdf_logs_on_failure(tmp_path):
    tex = tmp_path / "bad.tex"
    tex.write_text(
        "\\documentclass{article}\\begin{document}\\nonexistingcommand\\end{document}",
        encoding="utf-8",
    )
    logger = get_logger("test", tmp_path)
    out_pdf = tmp_path / "out.pdf"
    compile_pdf(tex, out_pdf, logger)

    log_content = (tmp_path / "logs" / "build.log").read_text(encoding="utf-8")
    assert "STDERR" in log_content
    assert "nonexistingcommand" in log_content

