"""Gera a tabela consolidada de metadados RTRS prontos para análise."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import write_csv
from rtrs_pipeline.research_dataset import research_rows
from rtrs_pipeline.review import read_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monta tabela de pesquisa a partir de campos promovidos.")
    parser.add_argument("--metadata", type=Path, default=PROJECT_ROOT / "outputs/tables/calibrated/metadata_promoted_calibrated.csv")
    parser.add_argument("--crop-areas", type=Path, default=PROJECT_ROOT / "outputs/tables/crop_area_v3/promoted_resolved/crop_area_promoted.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/metadata_research_ready.csv")
    args = parser.parse_args(argv)
    rows = research_rows(read_csv(args.metadata), read_csv(args.crop_areas))
    write_csv(args.output, rows)
    print(f"Registros prontos para pesquisa: {len(rows)}")
    print(dict(Counter(row["promotion_status"] for row in rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
