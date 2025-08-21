from __future__ import annotations

"""Parse requirement lists into a unified structure using LLM."""

import json
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from llm_client import LLMClient as Client
from .caching import LLMCache, llm_json
try:
    from tqdm import tqdm
except ModuleNotFoundError:  # pragma: no cover
    from contextlib import contextmanager

    @contextmanager
    def tqdm(*args, **kwargs):
        class Dummy:
            def update(self, *a, **k):
                pass

        yield Dummy()


@dataclass
class RequirementItem:
    """Standard requirement item."""

    id: str
    title: str
    keywords: List[str]
    source: str
    notes: str
    weight: float
    response_type: str = "generate"
    section: str = ""


def _from_dict(data: dict, index: int) -> RequirementItem:
    keywords = data.get("keywords", [])
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    return RequirementItem(
        id=str(data.get("id", index + 1)),
        title=str(data.get("title", "")),
        keywords=keywords,
        source=str(data.get("source", "")),
        notes=str(data.get("notes", "")),
        weight=float(data.get("weight", 1.0)),
        response_type=str(data.get("response_type", "generate")),
        section=str(data.get("section", "")),
    )


@dataclass
class FormatRequirement:
    """Requirements describing the desired document format/structure."""

    id: str
    section: str
    details: str


def _format_from_dict(data: dict, index: int) -> FormatRequirement:
    return FormatRequirement(
        id=str(data.get("id", index + 1)),
        section=str(data.get("section", "")),
        details=str(data.get("details", "")),
    )


def parse_requirements(path: Path, *, client: Client, cache: LLMCache, use_llm: bool = True) -> List[RequirementItem]:
    """Parse the requirement file into :class:`RequirementItem` objects.

    Supported formats include JSON/CSV/Markdown and PDF. PDF input relies on the
    LLM for structured extraction.
    """

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        if not use_llm:
            raise ValueError("PDF requirements need LLM parsing")
        try:
            from doc_loader import load_document  # type: ignore
        except ModuleNotFoundError:
            import importlib.util
            doc_path = Path(__file__).resolve().parent.parent / "scripts" / "doc_loader.py"
            spec = importlib.util.spec_from_file_location("doc_loader", doc_path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            load_document = getattr(module, "load_document")
        text = load_document(path)
    else:
        text = path.read_text(encoding="utf-8")

    if use_llm:
        try:
            system = (
                "You convert requirement lists provided in JSON/CSV/Markdown/PDF into a JSON array "
                "of objects with fields id,title,keywords,source,notes,weight,response_type,section. keywords is a list of strings. "
                "response_type is either 'generate' for content to be written by the system or 'copy' for text that should be copied directly from the source. "
                "section is the related document section if specified. "
                "CRITICAL: Return ONLY valid JSON array, no explanations, no reasoning, no other text. "
                "Start with [ and end with ]. No text before or after the JSON."
            )
            user = f"Input content:\n{text}\nReturn JSON array only."
            data = llm_json(client, system, user, cache)
            items_raw = data if isinstance(data, list) else data.get("items", [])
        except Exception as e:
            # 不进行本地启发式解析，直接抛出以确保完全依赖LLM
            raise RuntimeError(f"LLM解析失败: {e}")
    else:
        if suffix == ".json":
            items_raw = json.loads(text)
        elif suffix == ".csv":
            reader = csv.DictReader(text.splitlines())
            items_raw = list(reader)
        else:
            # 在禁用LLM的情况下，不做启发式解析，要求输入为结构化格式
            raise ValueError("非结构化输入需要启用use_llm=True")
    
    # Convert raw items to RequirementItem objects
    items = []
    with tqdm(total=len(items_raw), desc="转换需求项", unit="项") as pbar:
        for i, item_raw in enumerate(items_raw):
            if isinstance(item_raw, dict):
                items.append(_from_dict(item_raw, i))
            else:
                # Handle simple string items
                items.append(RequirementItem(
                    id=str(i + 1),
                    title=str(item_raw),
                    keywords=[],
                    source="",
                    notes="",
                    weight=1.0,
                    response_type="generate",
                ))
            pbar.update(1)

    return items


def parse_format_requirements(path: Path, *, client: Client, cache: LLMCache, use_llm: bool = True) -> List[FormatRequirement]:
    """Parse bid format requirements from a document."""

    text = path.read_text(encoding="utf-8")
    if not use_llm:
        raise ValueError("Parsing format requirements requires use_llm=True")

    system = (
        "You extract bid document format requirements into a JSON array of objects "
        "with fields id,section,details. Return ONLY the JSON array."
    )
    user = f"Input content:\n{text}\nReturn JSON array only."
    data = llm_json(client, system, user, cache)
    items_raw = data if isinstance(data, list) else data.get("items", [])
    return [_format_from_dict(item, i) for i, item in enumerate(items_raw)]


def _fallback_parse(text: str) -> List[Dict]:
    """Fallback parsing for markdown files when LLM fails."""
    lines = text.split('\n')
    items = []
    current_item = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是标题行
        if line.startswith('**') and line.endswith('**'):
            if current_item:
                items.append(current_item)
            current_item = {
                "id": str(len(items) + 1),
                "title": line[2:-2],
                "keywords": [],
                "source": "",
                "notes": "",
                "weight": 1.0,
                "response_type": "generate",
            }
        elif line.startswith('- ') and current_item:
            # 添加详细信息到notes
            if "notes" not in current_item:
                current_item["notes"] = ""
            current_item["notes"] += line[2:] + " "
    
    # 添加最后一个项目
    if current_item:
        items.append(current_item)
    
    # 如果没有找到任何项目，创建默认项目
    if not items:
        items = [{
            "id": "1",
            "title": "招标文件要求提交文档清单",
            "keywords": ["招标", "文档", "清单"],
            "source": "招标文件",
            "notes": "包含招标文件中要求提交的所有文档和材料",
            "weight": 1.0,
            "response_type": "generate",
        }]
    
    return items

