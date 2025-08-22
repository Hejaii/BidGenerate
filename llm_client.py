"""LLM client for DashScope/通义千问.

This module wraps the DashScope SDK to provide a simple chat interface with
retry and rate limiting. All text understanding and generation tasks in this
project rely on this client so that we do not use any local heuristics or
regular expressions for semantic work.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
import time
from typing import Dict, List, Optional

import dashscope


DEFAULT_API_KEY = "sk-3d74bc95ba88479bb27bf3984ae911c2"


def _hash_messages(messages: List[Dict[str, str]]) -> str:
    """Return a short hash of messages for logging/manifest."""
    m = hashlib.sha256()
    for msg in messages:
        m.update(json.dumps(msg, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    return m.hexdigest()[:10]


@dataclass
class LLMClient:
    """Simple wrapper around DashScope's ChatCompletion API.
    The client cycles through a predefined list of models. After every two
    requests it waits one second. If the API returns a 400 status code the
    client automatically switches to the next model in the list.
    """


    models: Optional[List[str]] = None
    api_key: Optional[str] = None
    max_retries: int = 3
    temperature: float = 0.2
    max_tokens: int = 4000
    _model_index: int = field(init=False, default=2)  # 从第三个模型开始，跳过前两个已用完免费额度的模型
    _request_counter: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("DASHSCOPE_API_KEY") or DEFAULT_API_KEY

        if self.models is None:
            self.models = [
                "qwen-plus-1220",
                "qwen-plus-0112",
                "qwen-plus-0919",
                "qwen-plus-0723",
                "qwen-plus-0806",
            ]
        
        # 确保模型索引在有效范围内
        if self._model_index >= len(self.models):
            self._model_index = 0
            
        dashscope.api_key = self.api_key

    @property
    def model(self) -> str:
        return self.models[self._model_index]

    def _rotate_model(self) -> None:
        print(f"🔄 从模型 {self.model} 切换到下一个模型...")
        self._model_index += 1
        if self._model_index >= len(self.models):
            print("⚠️  所有模型都已尝试，重置到第一个模型")
            self._model_index = 0
        print(f"✅ 现在使用模型: {self.model}")

    def chat(self, messages: List[Dict[str, str]], *,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None) -> str:
        """Send chat messages to the model and return the response text."""
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        attempt = 0
        while True:
            try:
                # 创建 Conversation 实例
                conversation = dashscope.aigc.conversation.Conversation()
                response = conversation.call(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                self._request_counter += 1
                if self._request_counter % 2 == 0:
                    time.sleep(1)

                if response.status_code == 200:
                    output = getattr(response.output, "text", None)
                    if output is None:
                        try:
                            output = response.output["choices"][0]["message"]["content"]
                        except (KeyError, TypeError, IndexError):
                            raise RuntimeError("Unexpected response format")
                    return output
                elif response.status_code == 403 and "free tier" in response.message.lower():
                    print(f"⚠️  模型 {self.model} 免费额度已用完，切换到下一个模型...")
                    self._rotate_model()
                    continue
                else:
                    raise RuntimeError(
                        f"Model call failed with status {response.status_code}: {response.message}"
                    )
            except Exception:
                attempt += 1
                if attempt >= self.max_retries:
                    raise
                time.sleep(2 ** attempt)

    def chat_json(self, messages: List[Dict[str, str]], *,
                  temperature: Optional[float] = None,
                  max_tokens: Optional[int] = None) -> Dict:
        """Call :py:meth:`chat` and parse the result as JSON."""
        text = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            # Surface the raw text to help debugging.
            raise ValueError(f"LLM output is not valid JSON: {text}") from exc
