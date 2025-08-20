"""Search and read evidence files from a repository."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

from doc_loader import load_document


def search_files(root: str | Path, patterns: Iterable[str]) -> List[Path]:
    """Return a list of paths under ``root`` matching glob ``patterns``."""
    root_path = Path(root)
    matches: List[Path] = []
    for pattern in patterns:
        matches.extend(root_path.glob(pattern))
    return [p for p in matches if p.is_file()]


def read_files(paths: Iterable[str | Path]) -> Dict[str, str]:
    """Read multiple documents and return mapping from path to text."""
    contents: Dict[str, str] = {}
    for p in paths:
        path = Path(p)
        try:
            contents[str(path)] = load_document(path)
        except Exception:
            continue
    return contents
