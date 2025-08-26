from __future__ import annotations

"""Generate bid content using outline-first strategy and simple concatenation."""

from pathlib import Path
from typing import Dict, List, Tuple
import re

from llm_client import LLMClient as Client
from .prompts_text import OUTLINE_SYSTEM, OUTLINE_USER, SEGMENT_SYSTEM, SEGMENT_USER
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


def _write_outline(requirement: RequirementItem, context: str, *, client: Client, cache: LLMCache) -> str:
    """Use LLM to draft an outline for the given requirement."""

    system = OUTLINE_SYSTEM
    req_title = requirement.title
    req_text = requirement.notes.strip() if getattr(requirement, "notes", "").strip() else requirement.title
    user = OUTLINE_USER.format(requirement_title=req_title, requirement_text=req_text, context=context)
    return llm_rewrite(client, system, user, cache)


def _generate_segment(
    requirement: RequirementItem,
    outline_item: str,
    context: str,
    prev: str,
    *,
    client: Client,
    cache: LLMCache,
) -> str:
    """Generate a segment for one outline item, ensuring coherence with previous text."""

    system = SEGMENT_SYSTEM
    req_title = requirement.title
    req_text = requirement.notes.strip() if getattr(requirement, "notes", "").strip() else requirement.title
    user = SEGMENT_USER.format(requirement_title=req_title, requirement_text=req_text, context=context, outline_item=outline_item, prev=prev)
    return llm_rewrite(client, system, user, cache)


def merge_contents(
    requirements: List[RequirementItem],
    ranked: Dict[str, List[Tuple[Path, float]]],
    *,
    client: Client,
    cache: LLMCache,
    use_llm: bool = True,
    output_dir: Path | None = None,
) -> tuple[str, Dict]:
    """Generate content via outline and segment generation then concatenate.

    If ``output_dir`` is provided, write each requirement's markdown response
    to a separate file within that directory.
    """

    sections: List[str] = []
    meta: Dict[str, Dict] = {}

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    with tqdm(total=len(requirements), desc="生成内容", unit="需求") as pbar:
        for req in requirements:
            files = ranked.get(req.id, [])
            meta_item: Dict = {"title": req.title, "candidates": []}
            snippets: List[str] = []

            for path, score in files:
                meta_item["candidates"].append({"path": str(path), "score": score})
                try:
                    snippet = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                snippets.append(snippet.strip())

            if not snippets:
                placeholder = f"针对招标要求 '{req.title}' 的响应内容正在准备中。"
                section_md = f"## {req.title}\n\n{placeholder}\n"
                meta_item["selected"] = None
            else:
                context = "\n\n".join(snippets)
                if use_llm:
                    try:
                        # 简化内容生成，避免重复
                        system = (
                            "你是一名专业的投标文件撰写专家。请根据招标要求和源文本，生成高质量的投标文件内容。\n\n"
                            "具体要求：\n"
                            "1. 内容必须直接针对招标要求，具有明确的针对性\n"
                            "2. 生成的内容应该是投标文件的具体组成部分，如技术方案、实施方案、管理方案等\n"
                            "3. 避免生成通用的、泛化的内容\n"
                            "4. 使用专业的技术术语和行业标准\n"
                            "5. 内容结构清晰，逻辑性强\n"
                            "6. 返回纯文本段落，不要Markdown格式\n"
                            "7. 内容要具体、可操作，避免空泛的描述\n"
                            "8. 每个段落要有明确的主题和重点\n\n"
                            "请生成高质量的投标文件内容。",
                        )
                        user = f"招标要求: {req.title}\n\n源文本:\n{context}"
                        merged = llm_rewrite(client, system, user, cache)
                        meta_item["outline"] = "简化生成"
                    except Exception as e:
                        print(f"⚠️ 内容生成失败: {e}，使用原始内容")
                        merged = context
                else:
                    merged = context

                if not merged.strip().endswith("\\newpage"):
                    merged = merged.rstrip() + "\n\\newpage"

                if req.title == "默认需求":
                    section_title = "项目技术方案与实施方案"
                else:
                    section_title = req.title

                section_md = f"# {section_title}\n\n{merged}\n"
                meta_item["selected"] = [str(p) for p, _ in files]

            sections.append(section_md)

            if output_dir is not None:
                safe_title = re.sub(r"[^a-zA-Z0-9_-]+", "_", req.title).strip("_")
                file_path = output_dir / f"{req.id}_{safe_title}.md"
                file_path.write_text(section_md, encoding="utf-8")

            meta[req.id] = meta_item
            pbar.update(1)

    merged_markdown = "\n".join(sections)
    return merged_markdown, meta
