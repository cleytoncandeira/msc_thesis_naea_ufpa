"""Gera resolução rastreável de área certificada/cultivada/total."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.area_resolution import read_candidates, resolve_area, write_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve origem de área sem usar área total como fallback.")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = resolve_area(read_candidates(args.candidates))
    write_csv(args.output, rows)
    print(f"Documentos com resolução de área: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
