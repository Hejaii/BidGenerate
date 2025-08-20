from pathlib import Path
from src.requirements_parser import parse_requirements
from src.caching import LLMCache


class DummyClient:
    def chat(self, messages, temperature=None, max_tokens=None):
        return '[{"id": "1", "title": "测试", "keywords": ["k"], "source": "", "notes": "", "weight": 1}]'


def test_parse_requirements_llm(tmp_path):
    req_file = tmp_path / "req.md"
    req_file.write_text("|id|title|\n|--|--|\n|1|a|", encoding="utf-8")
    items = parse_requirements(req_file, client=DummyClient(), cache=LLMCache(tmp_path / "cache"), use_llm=True)
    assert items[0].title == "测试"
