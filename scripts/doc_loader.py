"""Utilities for loading different document formats as plain text."""
from __future__ import annotations

from pathlib import Path

import pdfplumber
from docx import Document


def load_pdf(path: Path) -> str:
    """Load text from a PDF using pdfplumber."""
    with pdfplumber.open(path) as pdf:
        texts = [(page.extract_text() or "") for page in pdf.pages]
    return "\n".join(texts)


def load_docx(path: Path) -> str:
    """Load text from a DOCX file."""
    document = Document(path)
    return "\n".join(p.text for p in document.paragraphs)


def load_text(path: Path) -> str:
    """Load text from a UTF-8 plain text/markdown file."""
    return path.read_text(encoding="utf-8")


def load_document(path: str | Path) -> str:
    """Dispatch to the appropriate loader based on suffix."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(p)
    if suffix in {".docx", ".doc"}:
        return load_docx(p)
    if suffix in {".md", ".txt"}:
        return load_text(p)
    raise ValueError(f"Unsupported file type: {suffix}")
