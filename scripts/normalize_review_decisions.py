"""Gera cópia de revisão com correções explícitas semanticamente normalizadas."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.review import normalize_explicit_corrections, read_csv, write_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normaliza decisões com corrected_value já preenchido.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = read_csv(args.input)
    changed = normalize_explicit_corrections(rows)
    write_csv(args.output, rows)
    print(f"Linhas normalizadas: {changed}; arquivo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
