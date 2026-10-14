"""Prepara tabela larga e relatório de cobertura para análise RTRS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.analysis_table import pivot_research_rows
from rtrs_pipeline.consolidation import write_csv
from rtrs_pipeline.review import read_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera tabela analítica por documento a partir de metadados promovidos.")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready/metadata_research_ready_v2.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/tables/research_ready")
    args = parser.parse_args(argv)
    wide, coverage = pivot_research_rows(read_csv(args.input))
    write_csv(args.output_dir / "rtrs_document_analysis_table.csv", wide)
    write_csv(args.output_dir / "rtrs_document_field_coverage.csv", coverage)
    print(f"Documentos: {len(wide)}; campos: {len(coverage)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
