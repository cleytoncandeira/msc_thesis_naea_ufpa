"""Gera relação rastreável entre documentos e fazendas do legado."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import write_csv
from rtrs_pipeline.farm_linkage import document_farm_rows
from rtrs_pipeline.review import read_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Liga documentos RTRS às fazendas georreferenciadas do legado.")
    parser.add_argument("--register", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/rtrs_document_analysis_register.csv")
    parser.add_argument("--farms", type=Path, default=PROJECT_ROOT / "data/processed_data/farm_branches.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/document_farm_locations.csv")
    args = parser.parse_args(argv)
    with args.farms.open(encoding="utf-8", errors="replace", newline="") as handle:
        farms = list(csv.DictReader(handle))
    rows = document_farm_rows(read_csv(args.register), farms)
    write_csv(args.output, rows)
    print(f"Vínculos documento–fazenda: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
