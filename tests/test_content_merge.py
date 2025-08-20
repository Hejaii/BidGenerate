from pathlib import Path

from src.content_merge import merge_contents
from src.requirements_parser import RequirementItem


class DummyClient:
    pass


class DummyCache:
    pass


def test_merge_contents_no_llm(tmp_path: Path) -> None:
    snippet = tmp_path / "snippet.txt"
    snippet.write_text("示例内容", encoding="utf-8")
    req = RequirementItem(id="1", title="测试需求", keywords=[], source="", notes="", weight=1.0)

    merged, meta = merge_contents(
        [req], {"1": [(snippet, 0.9)]}, client=DummyClient(), cache=DummyCache(), use_llm=False
    )

    assert "示例内容" in merged
    assert "\\newpage" in merged
    assert meta["1"]["selected"] == [str(snippet)]
