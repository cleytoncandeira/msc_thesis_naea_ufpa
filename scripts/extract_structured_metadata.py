"""Fase 3: extrai metadados candidatos com proveniência por página."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.structured_extraction import (
    extract_metadata_from_page,
    read_jsonl,
    write_candidates_csv,
    write_jsonl,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extrai candidatos determinísticos dos relatórios RTRS.")
    parser.add_argument("--native-pages", type=Path, default=PROJECT_ROOT / "outputs/intermediate/pages_native.jsonl")
    parser.add_argument("--ocr-pages", type=Path, default=PROJECT_ROOT / "outputs/intermediate/ocr_text.jsonl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/tables")
    parser.add_argument("--prefix", default="metadata_candidates", help="Prefixo dos arquivos de saída; use outro para preservar uma rodada anterior.")
    args = parser.parse_args(argv)
    pages = list(read_jsonl(args.native_pages))
    if args.ocr_pages.exists():
        pages.extend(read_jsonl(args.ocr_pages))
    candidates = (candidate for page in pages for candidate in extract_metadata_from_page(page))
    jsonl_path = args.output_dir / f"{args.prefix}.jsonl"
    count = write_jsonl(jsonl_path, candidates)
    write_candidates_csv(jsonl_path, args.output_dir / f"{args.prefix}.csv")
    print(f"Candidatos de metadados: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
