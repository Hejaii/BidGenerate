from pathlib import Path
from pathlib import Path
from src.table_extractor import extract_tables, table_to_markdown, table_to_latex
from src.latex_renderer import markdown_to_latex
from src.caching import LLMCache


class DummyClient:
    def chat(self, messages, temperature=None, max_tokens=None):
        return "LaTeX"


def test_table_extraction_and_render(monkeypatch, tmp_path):
    class DummyPage:
        def extract_tables(self):
            return [[["H1", "H2"], ["C1", "C2"]]]

    class DummyPDF:
        pages = [DummyPage()]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def mock_open(path):
        return DummyPDF()

    monkeypatch.setattr("src.table_extractor.pdfplumber.open", mock_open)

    tables = extract_tables(Path("dummy.pdf"))
    assert tables == [[['H1', 'H2'], ['C1', 'C2']]]

    md = table_to_markdown(tables[0])
    cache = LLMCache(tmp_path / "cache")
    latex = markdown_to_latex(md, client=DummyClient(), cache=cache, use_llm=False)
    assert "\\begin{tabular}" in latex
    assert "H1" in latex and "C2" in latex

    latex_direct = table_to_latex(tables[0])
    assert "\\begin{tabular}" in latex_direct
    assert "H1" in latex_direct
