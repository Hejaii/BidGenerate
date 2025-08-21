from pathlib import Path
from src.requirements_parser import RequirementItem, parse_format_requirements
from src.outline_builder import build_outline, generate_bid
from src.caching import LLMCache


class DummyClient:
    def chat(self, messages, temperature=None, max_tokens=None):
        user = messages[1]["content"]
        if user.startswith("Outline:"):
            return "BID"
        return '[{"id": "1", "section": "封面", "details": "A4纸"}]'


def test_parse_format_and_generate(tmp_path: Path):
    fmt_file = tmp_path / "fmt.txt"
    fmt_file.write_text("format text", encoding="utf-8")
    client = DummyClient()
    cache = LLMCache(tmp_path / "cache")

    format_reqs = parse_format_requirements(fmt_file, client=client, cache=cache, use_llm=True)
    assert format_reqs[0].section == "封面"

    content = [RequirementItem(id="1", title="项目概述", keywords=[], source="", notes="简要介绍", weight=1.0, section="封面")]
    outline = build_outline(format_reqs, content)
    assert "项目概述" in outline
    assert "A4纸" in outline

    bid = generate_bid(outline, client=client, cache=cache, use_llm=True)
    assert bid == "BID"
