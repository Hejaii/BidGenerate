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
                        "你是一名专业的投标文件撰写专家。请根据招标要求和源文本，生成针对性的投标文件内容。\n\n"
                        "要求：\n"
                        "1. 内容必须直接针对招标要求，具有明确的针对性\n"
                        "2. 生成的内容应该是投标文件的具体组成部分，如技术方案、实施方案、管理方案等\n"
                        "3. 避免生成通用的、泛化的内容\n"
                        "4. 使用专业的技术术语和行业标准\n"
                        "5. 内容结构清晰，逻辑性强\n"
                        "6. 返回纯文本段落，不要Markdown格式\n\n"
                        "请生成高质量的投标文件内容。"
                    )
                    user = f"招标要求: {req.title}\n\n源文本:\n{snippet}"
                    rewritten = llm_rewrite(client, system, user, cache)
                    parts.append(rewritten.strip())
                else:
                    parts.append(snippet.strip())

            if not parts:
                placeholder = f"针对招标要求 '{req.title}' 的响应内容正在准备中。"
                sections.append(f"## {req.title}\n\n{placeholder}\n")
                meta_item["selected"] = None
            else:
                merged = "\n\n".join(parts)
                if not merged.strip().endswith("\\newpage"):
                    merged = merged.rstrip() + "\n\\newpage"

                # 生成更有意义的标题
                if req.title == "默认需求":
                    section_title = "项目技术方案与实施方案"
                else:
                    section_title = req.title
                
                sections.append(f"# {section_title}\n\n{merged}\n")
                meta_item["selected"] = [str(p) for p, _ in files]

            meta[req.id] = meta_item
            pbar.update(1)

    merged_markdown = "\n".join(sections)
    return merged_markdown, meta
