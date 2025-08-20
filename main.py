"""CLI entry point for automatic tender response generation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from analysis_parser import parse_analysis
from attachment_generator import generate_attachment
from chapter_extractor import extract_chapter
from doc_loader import load_document
from file_search import read_files, search_files
from llm_client import LLMClient
from response_writer import write_response
from utils import dump_json, ensure_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="自动生成投标响应文件")
    parser.add_argument("--analysis", required=True, help="分析表 TXT")
    parser.add_argument("--tender", required=True, help="标书全文文件")
    parser.add_argument("--repo", required=True, help="资料库根目录")
    parser.add_argument("--out", default="./output", help="输出目录")
    args = parser.parse_args()

    out_dir = Path(args.out)
    attachments_dir = out_dir / "attachments"
    responses_dir = out_dir / "responses"
    logs_dir = out_dir / "logs"

    ensure_dir(attachments_dir)
    ensure_dir(responses_dir)
    ensure_dir(logs_dir)

    llm = LLMClient()

    print("解析分析表...")
    analysis = parse_analysis(args.analysis, llm)

    print("读取标书...")
    tender_text = load_document(args.tender)

    print("抽取响应文件格式及附件章节...")
    chapter = extract_chapter(tender_text, llm)

    manifest: Dict[str, List[str]] = {"attachments": [], "responses": []}

    print("生成附件...")
    evidence_files = search_files(args.repo, ["**/*.md", "**/*.txt", "**/*.docx", "**/*.pdf"])
    evidence_texts = read_files(evidence_files)
    for spec in chapter.get("attachments_spec", []):
        path = generate_attachment(spec, analysis, evidence_texts, llm, attachments_dir)
        manifest["attachments"].append(str(path))

    print("生成逐条响应...")
    for req in analysis.get("requirements", []):
        path = write_response(req, evidence_texts, llm, responses_dir)
        manifest["responses"].append(str(path))

    dump_json(out_dir / "manifest.json", {"chapter": chapter, **manifest})
    print("完成。输出目录:", out_dir)


if __name__ == "__main__":
    main()
