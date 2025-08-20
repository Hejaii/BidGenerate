from __future__ import annotations

"""Knowledge base scanning and LLM-based ranking."""

from pathlib import Path
from typing import Dict, List, Tuple

from llm_client import LLMClient as Client
from .caching import LLMCache, llm_json
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


def scan_kb(kb_dir: Path) -> List[Path]:
    """Return all files under ``kb_dir``, limited to first 5 pages for testing."""
    all_files = [p for p in kb_dir.rglob('*') if p.is_file()]
    
    # 限制只处理前5个文件，避免处理时间过长
    print(f"📚 发现 {len(all_files)} 个文件，限制处理前5个用于测试")
    return all_files[:5]


def rank_files(requirement: RequirementItem, files: List[Path], *, topk: int, client: Client, cache: LLMCache, use_llm: bool = True) -> List[Tuple[Path, float]]:
    """Score and rank files for a requirement."""
    scores: List[Tuple[Path, float]] = []
    with tqdm(total=len(files), desc=f"评分 {requirement.title[:20]}...", unit="文件", leave=False) as pbar:
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                pbar.update(1)
                continue
            snippet = text[:800]
            if use_llm:
                system = (
                    "Given a requirement and a file snippet, score the relevance between 0 and 1 "
                    "and return JSON {\"score\": float}. "
                    "CRITICAL: Return ONLY valid JSON, no explanations, no reasoning, no other text. "
                    "Start with { and end with }. No text before or after the JSON."
                )
                user = (
                    f"Requirement: {requirement.title}\nKeywords: {', '.join(requirement.keywords)}\n"
                    f"File: {path.name}\nSnippet:\n{snippet}"
                )
                data = llm_json(client, system, user, cache)
                score = float(data.get("score", 0.0))
            else:
                # 禁止本地启发式评分，确保完全依赖LLM
                raise ValueError("必须启用use_llm=True以进行相关性评分")
            scores.append((path, score))
            pbar.update(1)
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:topk]
