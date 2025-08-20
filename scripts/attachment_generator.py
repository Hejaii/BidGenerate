"""Generate attachments according to the tender requirements."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from llm_client import LLMClient
from utils import ensure_dir, markdown_to_pdf, write_text

ATTACHMENT_PROMPT = (
    "你是一名投标附件生成器。根据给定的附件规范、分析表摘要和参考资料，"
    "生成符合要求的 Markdown 内容。保持字段顺序，并在需要签章/签字的地方标注。"
    '输出 JSON {"content": str, "source_refs": [], "placeholders": []}.'
)

CHECK_PROMPT = (
    "请根据附件规范检查以下内容是否满足所有字段、版式和约束要求。"
    "若有缺失，返回修订后的完整内容；若合格，原样返回。"
)


def generate_attachment(spec: Dict, analysis: Dict, evidence: Dict[str, str],
                        llm: LLMClient, out_dir: Path) -> Path:
    """Generate a single attachment file and return its path."""
    messages = [
        {"role": "system", "content": ATTACHMENT_PROMPT},
        {"role": "user", "content": json.dumps({
            "spec": spec,
            "analysis_summary": analysis.get("notes", ""),
            "evidence": evidence,
        }, ensure_ascii=False)},
    ]
    result = llm.chat_json(messages)
    content = result.get("content", "")

    check_messages = [
        {"role": "system", "content": CHECK_PROMPT},
        {"role": "user", "content": json.dumps({"spec": spec, "draft": content}, ensure_ascii=False)},
    ]
    checked = llm.chat_json(check_messages).get("content", content)

    filename = f"{spec['name'].replace(' ', '_')}.md"
    md_path = out_dir / filename
    ensure_dir(md_path.parent)
    write_text(md_path, checked)
    pdf_path = markdown_to_pdf(md_path)
    return pdf_path
