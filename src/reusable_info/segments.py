from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class CandidateSegment:
    """A raw segment extracted from a PDF page."""

    page: int
    bbox: Tuple[float, float, float, float]
    kind: str  # "text" or "image"
    content: str  # text content or OCR result


@dataclass
class KnowledgeEntry:
    """Structured information stored in the knowledge base."""

    type: str
    source_pdf: str
    page: int
    bbox: Tuple[float, float, float, float]
    fields: Optional[Dict[str, str]] = None
    file: Optional[str] = None  # path to cropped PDF for images
