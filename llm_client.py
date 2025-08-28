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
    # Maximum tokens allowed in the input context. This is a rough character
    # based approximation but helps avoid sending overly long prompts which
    # would be rejected by the API.
    max_input_tokens: int = 6000
    _model_index: int = field(init=False, default=2)  # 从第三个模型开始，跳过前两个已用完免费额度的模型
    _request_counter: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = DEFAULT_API_KEY

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
        # Make a shallow copy so modifications do not affect caller and caching
        # logic which relies on the original messages.
        messages = [dict(m) for m in messages]

        # Rough token counting using character length. If the combined input
        # exceeds ``max_input_tokens`` we truncate the last message so that the
        # request stays within the model's limit. This is a pragmatic safeguard
        # and does not aim for exact token parity with the model's tokenizer.
        total_len = sum(len(m.get("content", "")) for m in messages)
        if total_len > self.max_input_tokens and messages:
            allowed = self.max_input_tokens - (total_len - len(messages[-1].get("content", "")))
            if allowed < 0:
                allowed = 0
            messages[-1]["content"] = messages[-1].get("content", "")[:allowed]
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
