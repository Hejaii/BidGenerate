from __future__ import annotations

"""Regex-based field extraction for text segments."""

import re
from typing import Dict


def extract_fields(text: str, seg_type: str) -> Dict[str, str]:
    """Extract structured fields from ``text`` according to ``seg_type``.

    This uses simple regular expressions so that we do not rely on the LLM for
    deterministic parsing tasks.
    """

    fields: Dict[str, str] = {}
    if seg_type == "公司资质":
        if m := re.search(r"资质名称[:：]?\s*(\S+)", text):
            fields["资质名称"] = m.group(1)
        if m := re.search(r"证书编号[:：]?\s*(\S+)", text):
            fields["证书编号"] = m.group(1)
        if m := re.search(r"有效期[:：]?\s*([\d\-\.]+)", text):
            fields["有效期"] = m.group(1)
    elif seg_type == "负责人信息":
        if m := re.search(r"姓名[:：]?\s*(\S+)", text):
            fields["姓名"] = m.group(1)
        if m := re.search(r"电话[:：]?\s*(\S+)", text):
            fields["电话"] = m.group(1)
    return fields
