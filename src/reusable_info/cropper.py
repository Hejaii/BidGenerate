from __future__ import annotations

"""Utilities to crop segments from a PDF."""

from pathlib import Path

import fitz  # PyMuPDF

from .segments import CandidateSegment


def crop_to_pdf(pdf_path: str, seg: CandidateSegment, out_file: Path) -> None:
    """Crop ``seg`` from ``pdf_path`` and save it as ``out_file``."""

    doc = fitz.open(pdf_path)
    try:
        page = doc[seg.page - 1]
        rect = fitz.Rect(*seg.bbox)
        new_doc = fitz.open()
        new_page = new_doc.new_page(width=rect.width, height=rect.height)
        new_page.show_pdf_page(new_page.rect, doc, seg.page - 1, clip=rect)
        new_doc.save(out_file)
        new_doc.close()
    finally:
        doc.close()
