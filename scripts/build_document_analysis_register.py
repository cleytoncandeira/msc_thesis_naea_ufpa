"""Monta registro analítico documentar e candidatos de vínculo com a base histórica."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import write_csv
from rtrs_pipeline.legacy_linkage import link_legacy_rows
from rtrs_pipeline.review import read_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Une registro documental promovido e legado RTRS de forma conservadora.")
    parser.add_argument("--documents", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/rtrs_document_analysis_table.csv")
    parser.add_argument("--legacy", type=Path, default=PROJECT_ROOT / "data/processed_data/brazil_rtrs.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready")
    args = parser.parse_args(argv)
    documents = read_csv(args.documents)
    with args.legacy.open(encoding="latin1", newline="") as handle:
        legacy = list(csv.DictReader(handle))
    register, candidates = link_legacy_rows(documents, legacy)
    write_csv(args.output_dir / "rtrs_document_analysis_register.csv", register)
    write_csv(args.output_dir / "legacy_linkage_candidates.csv", candidates)
    print(f"Documentos: {len(register)}; candidatos de vínculo: {len(candidates)}")
    print(dict(Counter(row["legacy_match_status"] for row in register)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
