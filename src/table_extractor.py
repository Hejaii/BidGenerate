from __future__ import annotations

"""Utilities for extracting tables from PDFs and rendering them."""

from pathlib import Path
from typing import List

import pdfplumber


def extract_tables(path: Path) -> List[List[List[str]]]:
    """Extract tables from a PDF.

    Returns a list of tables, where each table is represented as a list of
    rows and each row is a list of cell strings.
    """
    tables: List[List[List[str]]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                # Normalize cells to strings and strip whitespace
                normalized = [[(cell or "").strip() for cell in row] for row in table]
                tables.append(normalized)
    return tables


def table_to_markdown(table: List[List[str]]) -> str:
    """Convert a table (list of rows) to Markdown format."""
    if not table:
        return ""
    header = table[0]
    md_lines = ["| " + " | ".join(header) + " |"]
    md_lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in table[1:]:
        md_lines.append("| " + " | ".join(row) + " |")
    return "\n".join(md_lines)


def table_to_latex(table: List[List[str]]) -> str:
    """Convert a table (list of rows) to a LaTeX tabular environment."""
    if not table:
        return ""
    cols = max(len(row) for row in table)
    col_spec = " | ".join(["l"] * cols)
    lines = [r"\begin{tabular}{" + col_spec + "}", r"\hline"]
    for row in table:
        cells = [escape_latex(cell) for cell in row]
        lines.append(" & ".join(cells) + r" \\")
        lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    return "\n".join(lines)


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in ``text``."""
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def extract_tables_to_latex(path: Path) -> List[str]:
    """Convenience wrapper returning LaTeX tables from ``path``."""
    return [table_to_latex(t) for t in extract_tables(path)]
