"""Gera fila preenchível para revisar vínculos entre documentos e legado."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import write_csv
from rtrs_pipeline.legacy_review import legacy_linkage_review_queue
from rtrs_pipeline.review import read_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara revisão manual de vínculos históricos RTRS.")
    parser.add_argument("--register", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/rtrs_document_analysis_register.csv")
    parser.add_argument("--candidates", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/legacy_linkage_candidates.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/validation/legacy_linkage_human_validation.csv")
    args = parser.parse_args(argv)
    rows = legacy_linkage_review_queue(read_csv(args.register), read_csv(args.candidates))
    write_csv(args.output, rows)
    print(f"Documentos para revisão de vínculo: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
