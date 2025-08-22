import os
import pytest

from src.pdf_builder import apply_project_config, format_bid_date, load_config


def test_format_bid_date_variants():
    assert format_bid_date("2023-12-01") == "2023年12月01日"
    assert format_bid_date("2023/12/01") == "2023年12月01日"
    assert format_bid_date("2023年12月1日") == "2023年12月01日"
    assert format_bid_date("2023年12月") == "2023年12月"


def test_apply_project_config_sets_env(monkeypatch):
    monkeypatch.delenv("PROJECT_NO", raising=False)
    monkeypatch.delenv("BID_DATE", raising=False)
    cfg = {"project_no": "ABC123", "bid_date": "2024-02-03", "bid_title": "示例"}
    apply_project_config(cfg)
    assert os.getenv("PROJECT_NO") == "ABC123"
    assert os.getenv("BID_DATE") == "2024年02月03日"
    assert os.getenv("BID_TITLE") == "示例"


def test_apply_project_config_missing(monkeypatch):
    with pytest.raises(ValueError):
        apply_project_config({"project_no": "ONLY"})


def test_load_config_from_path(tmp_path):
    cfg_path = tmp_path / "custom.toml"
    cfg_path.write_text(
        """
        [tool.build_pdf.project]
        project_no = "X-1"
        bid_date = "2025-01-02"
        """,
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert cfg["project"]["project_no"] == "X-1"
