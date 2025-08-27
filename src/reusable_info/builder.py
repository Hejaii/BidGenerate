from __future__ import annotations

"""High level pipeline to build a knowledge base from PDFs."""

from dataclasses import asdict
import json
from pathlib import Path
from typing import List

from .classifier import LLMClassifier, SegmentClassifier
from .cropper import crop_to_pdf
from .extract import extract_candidates
from .fields import extract_fields
from .segments import KnowledgeEntry


def build_knowledge_base(
    pdf_path: str,
    out_dir: str,
    classifier: SegmentClassifier | None = None,
) -> List[KnowledgeEntry]:
    """Process ``pdf_path`` and create a knowledge base under ``out_dir``."""

    classifier = classifier or LLMClassifier()
    pdf_path = str(pdf_path)
    out_root = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    entries: List[KnowledgeEntry] = []
    for seg in extract_candidates(pdf_path):
        seg_type = classifier.classify(seg)
        if seg_type == "证件图片":
            out_file = out_root / f"page{seg.page}_x{int(seg.bbox[0])}_y{int(seg.bbox[1])}.pdf"
            crop_to_pdf(pdf_path, seg, out_file)
            entry = KnowledgeEntry(
                type=seg_type,
                source_pdf=pdf_path,
                page=seg.page,
                bbox=seg.bbox,
                file=str(out_file),
            )
            entries.append(entry)
        elif seg_type in {"公司资质", "负责人信息"}:
            fields = extract_fields(seg.content, seg_type)
            entry = KnowledgeEntry(
                type=seg_type,
                source_pdf=pdf_path,
                page=seg.page,
                bbox=seg.bbox,
                fields=fields,
            )
            entries.append(entry)
        # ignore "其他"

    with open(out_root / "knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in entries], f, ensure_ascii=False, indent=2)

    return entries
