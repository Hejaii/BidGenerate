from __future__ import annotations

"""Simple local cache for LLM calls to avoid repeated charges."""

import hashlib
import json
from pathlib import Path
from typing import Dict, List
import logging

from llm_client import LLMClient as Client  # alias as Client per instructions


class LLMCache:
    """Disk-based cache for LLM requests."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, messages: List[Dict[str, str]]) -> str:
        m = hashlib.sha256()
        for msg in messages:
            m.update(json.dumps(msg, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        return m.hexdigest()

    def get(self, messages: List[Dict[str, str]]) -> str | None:
        key = self._key(messages)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def set(self, messages: List[Dict[str, str]], value: str) -> None:
        key = self._key(messages)
        path = self.cache_dir / f"{key}.json"
        path.write_text(value, encoding="utf-8")


def llm_json(client: Client, system: str, user: str, cache: LLMCache, *, logger: logging.Logger | None = None) -> Dict:
    """Call LLM with caching and expect a JSON response."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    if logger:
        import inspect
        logger.debug("LLMClient.chat signature: %s", inspect.signature(client.chat))
    cached = cache.get(messages)
    if cached is not None:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            # 缓存的数据损坏，删除缓存
            cache.set(messages, "")
    
    text = client.chat(messages)
    
    # 清理LLM返回的文本，只保留JSON部分
    text = text.strip()
    if text.startswith('```json'):
        text = text[7:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()
    
    try:
        data = json.loads(text)
        cache.set(messages, json.dumps(data, ensure_ascii=False))
        return data
    except json.JSONDecodeError:
        # 尝试修复JSON - 提取JSON部分
        print(f"⚠️  JSON解析失败，尝试提取JSON部分: {text[:100]}...")
        
        # 尝试找到JSON开始和结束位置
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_text = text[json_start:json_end]
            try:
                data = json.loads(json_text)
                cache.set(messages, json.dumps(data, ensure_ascii=False))
                return data
            except json.JSONDecodeError:
                pass
        
        # 如果提取失败，尝试修复
        repair_user = f"The previous response was not valid JSON: {text}. Please return ONLY valid JSON, no explanations, no reasoning, no other text."
        text = client.chat([
            {"role": "system", "content": system + " IMPORTANT: Return ONLY valid JSON, no other text."},
            {"role": "user", "content": repair_user},
        ])
        
        # 清理修复后的文本
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        # 再次尝试提取JSON
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_text = text[json_start:json_end]
            try:
                data = json.loads(json_text)
                cache.set(messages, json.dumps(data, ensure_ascii=False))
                return data
            except json.JSONDecodeError:
                pass
        
        # 如果修复失败，返回默认结构
        print(f"⚠️  JSON修复失败，使用默认结构: {text[:100]}...")
        default_data = {"items": [{"id": "1", "title": "默认需求", "keywords": [], "source": "", "notes": "", "weight": 1.0}]}
        cache.set(messages, json.dumps(default_data, ensure_ascii=False))
        return default_data


def llm_rewrite(client: Client, system: str, user: str, cache: LLMCache) -> str:
    """Call LLM with caching for text generation or rewriting."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    cached = cache.get(messages)
    if cached is not None:
        return cached
    text = client.chat(messages)
    cache.set(messages, text)
    return text
