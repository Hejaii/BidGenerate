"""Miscellaneous utility helpers."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


def ensure_dir(path: Path) -> None:
    """Ensure parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to ``path``."""
    ensure_dir(path)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: Any) -> None:
    ensure_dir(path)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def markdown_to_pdf(md_path: Path) -> Path:

    """Convert a Markdown file to a simple PDF without external deps."""
    text = md_path.read_text(encoding="utf-8")
    pdf_path = md_path.with_suffix(".pdf")
    lines = text.splitlines()

    def escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    y_start = 760
    line_height = 14
    content = ["BT", "/F1 12 Tf", f"72 {y_start} Td"]
    for line in lines:
        content.append(f"({escape(line)}) Tj")
        content.append(f"0 -{line_height} Td")
    content.append("ET")
    content_stream = "\n".join(content)

    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >> endobj",
        f"4 0 obj << /Length {len(content_stream.encode('latin-1'))} >> stream\n{content_stream}\nendstream endobj",
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    ]

    pdf_bytes = ["%PDF-1.4"]
    xref_positions = [0]
    offset = len("%PDF-1.4\n".encode("latin-1"))
    for obj in objects:
        xref_positions.append(offset)
        pdf_bytes.append(obj)
        offset += len(obj.encode("latin-1")) + 1
    xref_start = offset
    xref = ["xref", f"0 {len(xref_positions)}", "0000000000 65535 f "]
    for pos in xref_positions[1:]:
        xref.append(f"{pos:010d} 00000 n ")
    trailer = f"trailer << /Size {len(xref_positions)} /Root 1 0 R >>"
    pdf_bytes.extend(xref)
    pdf_bytes.append(trailer)
    pdf_bytes.append(f"startxref\n{xref_start}\n%%EOF")

    ensure_dir(pdf_path)
    pdf_path.write_bytes("\n".join(pdf_bytes).encode("latin-1"))

    return pdf_path
