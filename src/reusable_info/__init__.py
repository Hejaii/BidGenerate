"""Utilities for extracting reusable information from PDFs."""

from .builder import build_knowledge_base
from .segments import CandidateSegment, KnowledgeEntry

__all__ = [
    "build_knowledge_base",
    "CandidateSegment",
    "KnowledgeEntry",
]
