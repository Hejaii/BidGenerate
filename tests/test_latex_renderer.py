from pathlib import Path
from src.latex_renderer import markdown_to_latex, render_main_tex
from src.caching import LLMCache


class DummyClient:
    def chat(self, messages, temperature=None, max_tokens=None):
        return "LaTeX"


def test_render(tmp_path):
    cache = LLMCache(tmp_path / "cache")
    md = "# Title"
    latex = markdown_to_latex(md, client=DummyClient(), cache=cache, use_llm=False)
    template = Path("templates/main.tex")
    out = tmp_path / "main.tex"
    render_main_tex(latex, template, out)
    assert out.read_text(encoding="utf-8").strip() != ""
