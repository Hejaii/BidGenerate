from pathlib import Path
from src.kb_search import rank_files
from src.caching import LLMCache
from src.requirements_parser import RequirementItem


class DummyClient:
    def chat(self, messages, temperature=None, max_tokens=None):
        # 返回一个JSON评分
        return '{"score": 0.9}'


def fake_llm_json(client, system, user, cache):
    if "file1" in user:
        return {"score": 0.9}
    return {"score": 0.1}


def test_rank_files(monkeypatch, tmp_path):
    f1 = tmp_path / "file1.txt"
    f1.write_text("hello", encoding="utf-8")
    f2 = tmp_path / "file2.txt"
    f2.write_text("world", encoding="utf-8")
    req = RequirementItem(id="1", title="t", keywords=["hello"], source="", notes="", weight=1)
    from src import kb_search as ks
    monkeypatch.setattr(ks, "llm_json", fake_llm_json)
    ranked = rank_files(req, [f1, f2], topk=2, client=DummyClient(), cache=LLMCache(tmp_path / "cache"), use_llm=True)
    assert ranked[0][0] == f1
