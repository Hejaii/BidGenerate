"""Extract the '响应文件格式及附件' chapter from the tender document."""
from __future__ import annotations

from typing import Dict

from llm_client import LLMClient

CHAPTER_PROMPT = (
    "你是一名投标文件解析助手。给定招标文件全文，找出标题为“响应文件格式及附件”的章节，"
    '返回 JSON: {"chapter_title": str, "start_index": int, "end_index": int, '
    '"raw_text": str, "attachments_spec": []}。'
    "attachments_spec 每项包含 name, required_format, fields, layout_notes, filetype, constraints。"
)


def extract_chapter(tender_text: str, llm: LLMClient) -> Dict:
    messages = [
        {"role": "system", "content": CHAPTER_PROMPT},
        {"role": "user", "content": tender_text},
    ]
    return llm.chat_json(messages)
