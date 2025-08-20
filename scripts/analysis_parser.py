"""Parse the analysis table using the LLM."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from llm_client import LLMClient

ANALYSIS_PROMPT = (
    "你是一名投标分析助手。请将以下分析表文本解析成 JSON。"
    '返回 schema 如下：{"requirements": [{"id": "", "title": "", "type": "", "page": "", '
    '"importance": "", "score_current": "", "scoring_rule": "", "strengths": [], '
    '"weaknesses": [], "advice": [], "evidence_files": []}], "notes": ""}'
)


def parse_analysis(path: str | Path, llm: LLMClient) -> Dict:
    """Send the entire analysis table to the LLM and parse it into JSON."""
    text = Path(path).read_text(encoding="utf-8")
    messages = [
        {"role": "system", "content": ANALYSIS_PROMPT},
        {"role": "user", "content": text},
    ]
    return llm.chat_json(messages)

