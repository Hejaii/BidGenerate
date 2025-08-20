#!/usr/bin/env python3
"""End-to-end pipeline: extract requirements then build PDF."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import logging

import pdfplumber

from scripts.pdf_extractor import QianwenAPI
from llm_client import LLMClient as Client
from src.caching import LLMCache
from src.requirements_parser import parse_requirements
from src.kb_search import scan_kb, rank_files
from src.content_merge import merge_contents
from src.latex_renderer import markdown_to_latex, render_main_tex
from src.pdf_builder import compile_pdf, load_config, DEFAULT_TEMPLATE


def extract_requirements(pdf_path: Path, api: QianwenAPI, out_path: Path) -> Path:
    """Extract requirement texts from a tender PDF into a markdown file."""
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            for req in api.extract_all_requirements(text, page_number):
                lines.append(f"- {req['requirement_text']}")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract requirements then build bid PDF")
    parser.add_argument("--tender", type=Path, required=True, help="招标PDF文件")
    parser.add_argument("--kb", type=Path, required=True, help="知识库目录")
    parser.add_argument("--out", type=Path, required=True, help="输出PDF路径")
    parser.add_argument("--workdir", type=Path, default=Path("build"), help="工作目录")
    parser.add_argument("--topk", type=int, default=3, help="每条需求选取的参考数量")
    args = parser.parse_args()

    workdir = args.workdir
    workdir.mkdir(parents=True, exist_ok=True)
    cache = LLMCache(workdir / "cache")
    config = load_config()
    temperature = config.get("temperature")
    client = Client(models=None, temperature=temperature if temperature is not None else 0.2)
    api = QianwenAPI(os.getenv("DASHSCOPE_API_KEY", ""))

    print("📄 提取需求...")
    req_md = extract_requirements(args.tender, api, workdir / "extracted_requirements.md")

    print("📋 解析需求...")
    requirements = parse_requirements(req_md, client=client, cache=cache, use_llm=True)

    print("🔍 扫描知识库...")
    files = scan_kb(args.kb)

    print("🎯 检索相关内容...")
    ranked = {item.id: rank_files(item, files, topk=args.topk, client=client, cache=cache, use_llm=True)
              for item in requirements}

    print("📝 生成并合并内容...")
    merged_md, meta = merge_contents(requirements, ranked, client=client, cache=cache, use_llm=True)
    md_path = workdir / "merged.md"
    md_path.write_text(merged_md, encoding="utf-8")

    print("🧵 转换为LaTeX...")
    latex_body = markdown_to_latex(merged_md, client=client, cache=cache, use_llm=True)
    tex_path = workdir / "main.tex"
    render_main_tex(latex_body, DEFAULT_TEMPLATE, tex_path)
    meta_path = workdir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("📄 编译PDF...")
    logger = logging.getLogger("full_pipeline")
    compile_pdf(tex_path, args.out, logger)
    print(f"✅ PDF生成完成: {args.out}")


if __name__ == "__main__":
    main()
