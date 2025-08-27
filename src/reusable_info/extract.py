from __future__ import annotations

"""Functions to extract candidate segments from PDF files."""

from typing import Iterable
import fitz  # PyMuPDF

from .segments import CandidateSegment


def extract_candidates(pdf_path: str) -> Iterable[CandidateSegment]:
    """Yield text and image blocks from ``pdf_path``.

    Uses :mod:`fitz` to obtain per-page blocks with coordinates. Text blocks
    contain their plain text, image blocks have empty ``content``.
    """

    doc = fitz.open(pdf_path)
    try:
        for page_number, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                bbox = tuple(block["bbox"])
                if block["type"] == 0:  # text block
                    text = "\n".join(
                        "".join(span["text"] for span in line["spans"])
                        for line in block.get("lines", [])
                    ).strip()
                    if text:
                        yield CandidateSegment(page_number, bbox, "text", text)
                elif block["type"] == 1:  # image block
                    yield CandidateSegment(page_number, bbox, "image", "")
    finally:
        doc.close()
