from __future__ import annotations

"""Merge selected knowledge base snippets into unified Markdown."""

from pathlib import Path
from typing import Dict, List, Tuple

from llm_client import LLMClient as Client
from .caching import LLMCache, llm_rewrite
from .requirements_parser import RequirementItem
try:
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover
    from contextlib import contextmanager

    @contextmanager
    def tqdm(*args, **kwargs):
        class Dummy:
            def update(self, *a, **k):
                pass

        yield Dummy()


def merge_contents(
    requirements: List[RequirementItem],
    ranked: Dict[str, List[Tuple[Path, float]]],
    *,
    client: Client,
    cache: LLMCache,
    use_llm: bool = True,
) -> tuple[str, Dict]:
    """Merge contents for requirements.

    Each knowledge base snippet is optionally rewritten via LLM so that the
    resulting text can be directly concatenated. The merge step itself only
    concatenates these pieces without additional LLM calls.

    Returns merged Markdown text and metadata mapping.
    """

    sections: List[str] = []
    meta: Dict[str, Dict] = {}

    with tqdm(total=len(requirements), desc="合并内容", unit="需求") as pbar:
        for req in requirements:
            files = ranked.get(req.id, [])
            meta_item = {"title": req.title, "candidates": []}
            parts: List[str] = []

            for path, score in files:
                meta_item["candidates"].append({"path": str(path), "score": score})
                try:
                    snippet = path.read_text(encoding="utf-8")
                except Exception:
                    continue

                if use_llm:
                    system = (
                        "Rewrite the source text so it directly addresses the given requirement. "
                        "Return plain paragraphs without Markdown formatting."
                    )
                    user = f"Requirement: {req.title}\nSource:\n{snippet}"
                    rewritten = llm_rewrite(client, system, user, cache)
                    parts.append(rewritten.strip())
                else:
                    parts.append(snippet.strip())

            if not parts:
                placeholder = f"未找到与需求 {req.title} 相关的内容。"
                sections.append(f"### {req.title}\n\n{placeholder}\n")
                meta_item["selected"] = None
            else:
                merged = "\n\n".join(parts)
                if not merged.strip().endswith("\\newpage"):
                    merged = merged.rstrip() + "\n\\newpage"
                sections.append(f"# {req.title}\n\n{merged}\n")
                meta_item["selected"] = [str(p) for p, _ in files]

            meta[req.id] = meta_item
            pbar.update(1)

    merged_markdown = "\n".join(sections)
    return merged_markdown, meta
