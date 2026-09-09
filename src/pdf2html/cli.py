from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import convert


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert a PDF to accessible, auditable HTML.")
    parser.add_argument("pdf", type=Path, help="Input PDF")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output directory")
    parser.add_argument("--dpi", type=int, default=144, help="Page-render resolution (default: 144)")
    parser.add_argument(
        "--pages",
        help="Pages to convert, for example 1,3,19-20. Omit to convert every page.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = convert(args.pdf, args.output, dpi=args.dpi, pages=args.pages)
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Converted {result.page_count} page(s) to {result.html_path}")
    if result.ocr_candidates:
        pages = ", ".join(map(str, result.ocr_candidates))
        print(f"Review/OCR recommended for page(s): {pages}")
    return 0
