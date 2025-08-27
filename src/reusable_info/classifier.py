from __future__ import annotations

"""Classification utilities for candidate segments."""

from typing import List

from llm_client import LLMClient

from .segments import CandidateSegment


class SegmentClassifier:
    """Base class for segment classifiers."""

    def classify(self, seg: CandidateSegment) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class LLMClassifier(SegmentClassifier):
    """Classify segments using an LLM."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()
        self.prompt = (
            "你是一个分类助手。判断给定片段属于 ['公司资质','负责人信息','证件图片','其他'] 之一，"
            "仅返回 JSON 格式 {\"type\": \"类别\"}。"
        )

    def classify(self, seg: CandidateSegment) -> str:
        content = seg.content if seg.kind == "text" else seg.content or ""
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": content},
        ]
        result = self.llm.chat_json(messages)
        return result.get("type", "其他")
