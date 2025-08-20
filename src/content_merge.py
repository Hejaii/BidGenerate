from __future__ import annotations

"""Merge selected knowledge base snippets into unified Markdown."""

import json
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


def merge_contents(requirements: List[RequirementItem], ranked: Dict[str, List[Tuple[Path, float]]], *, client: Client, cache: LLMCache, use_llm: bool = True) -> tuple[str, Dict]:
    """Merge contents for requirements.

    Returns merged Markdown text and metadata mapping.
    """
    sections: List[str] = []
    meta: Dict[str, Dict] = {}
    with tqdm(total=len(requirements), desc="合并内容", unit="需求") as pbar:
        for req in requirements:
            files = ranked.get(req.id, [])
            meta_item = {"title": req.title, "candidates": []}
            snippets: List[str] = []
            for path, score in files:
                meta_item["candidates"].append({"path": str(path), "score": score})
                try:
                    snippets.append(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
            if not snippets:
                placeholder = f"未找到与需求 {req.title} 相关的内容。"
                sections.append(f"### {req.title}\n\n{placeholder}\n")
                meta_item["selected"] = None
            else:
                if use_llm:
                    system = (
                        "Combine the following content pieces into a coherent text section. "
                        "Remove duplicates but keep references to original file paths. "
                        "DO NOT use any Markdown formatting like **, *, -, tables, or code fences. "
                        "Return plain paragraphs with simple line breaks only. "
                        "Append a line with \\newpage at the end so that each requirement starts on a new page."
                    )
                    user_parts = []
                    for (path, _), snippet in zip(files, snippets):
                        user_parts.append(f"Source: {path}\n{snippet}")
                    user = f"Requirement: {req.title}\n\n" + "\n\n".join(user_parts)
                    merged = llm_rewrite(client, system, user, cache)
                else:
                    merged = "\n\n".join(snippets)
                if not merged.strip().endswith("\\newpage"):
                    merged = merged.rstrip() + "\n\\newpage"
                # 将每个需求标题作为 Markdown 一级标题，以便 LaTeX 生成目录与章节
                sections.append(f"# {req.title}\n\n{merged}\n")
                meta_item["selected"] = [str(p) for p, _ in files]
            meta[req.id] = meta_item
            pbar.update(1)
    merged_markdown = "\n".join(sections)
    return merged_markdown, meta
