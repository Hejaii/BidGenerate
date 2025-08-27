#!/usr/bin/env python3
"""Build a knowledge base of reusable bid information from a PDF."""

from pathlib import Path
import argparse

from src.reusable_info.builder import build_knowledge_base


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract reusable info from bid PDF")
    parser.add_argument("pdf", help="Path to the bid PDF to process")
    parser.add_argument(
        "out", help="Directory where the knowledge base and cropped PDFs will be stored"
    )
    args = parser.parse_args()

    entries = build_knowledge_base(args.pdf, args.out)
    print(f"Saved {len(entries)} entries to {Path(args.out).resolve()}")


if __name__ == "__main__":
    main()
