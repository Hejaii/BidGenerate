from __future__ import annotations

"""Utilities for building bid document outlines and generating full text."""

from typing import List

from llm_client import LLMClient as Client
from .caching import LLMCache, llm_rewrite
from .requirements_parser import RequirementItem, FormatRequirement


def build_outline(format_reqs: List[FormatRequirement], content_reqs: List[RequirementItem]) -> str:
    """Generate a bid document outline.

    Each format requirement becomes a top-level section. Content requirements
    assigned to the same section are listed beneath it.
    """

    lines: List[str] = []
    for fmt in format_reqs:
        lines.append(f"# {fmt.section}")
        if fmt.details:
            lines.append(fmt.details)
        for item in content_reqs:
            if item.section == fmt.section:
                detail = f": {item.notes}" if item.notes else ""
                lines.append(f"- {item.title}{detail}")
        lines.append("")
    return "\n".join(lines).strip()


def generate_bid(outline: str, *, client: Client, cache: LLMCache, use_llm: bool = True) -> str:
    """Generate the final bid document text from an outline using LLM."""

    if not use_llm:
        return outline
    system = (
        "You are an expert bid writer. Based on the provided outline, write a complete "
        "bid document in Markdown."
    )
    user = f"Outline:\n{outline}\nWrite the bid document."
    return llm_rewrite(client, system, user, cache)
