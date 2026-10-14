"""Consolida e amostra candidatos de áreas de soja e milho para revisão."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import read_jsonl, write_csv
from rtrs_pipeline.crop_area import apply_known_decisions, crop_area_consensus, crop_area_validation_queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara validação de áreas separadas por cultura.")
    parser.add_argument("--candidates", type=Path, default=PROJECT_ROOT / "outputs/tables/metadata_candidates_crop_v3.jsonl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/tables/crop_area_v3")
    parser.add_argument("--validation-output", type=Path, default=PROJECT_ROOT / "outputs/validation/crop_area_human_validation.csv")
    parser.add_argument("--known-decisions", type=Path, default=PROJECT_ROOT / "outputs/validation/crop_area_known_decisions.csv")
    parser.add_argument("--single-sample-size", type=int, default=30)
    args = parser.parse_args(argv)
    rows = crop_area_consensus(list(read_jsonl(args.candidates)))
    write_csv(args.output_dir / "crop_area_field_consensus.csv", rows)
    queue = crop_area_validation_queue(rows, single_sample_size=args.single_sample_size)
    applied = 0
    if args.known_decisions.exists():
        with args.known_decisions.open(encoding="utf-8", newline="") as handle:
            applied = apply_known_decisions(queue, list(csv.DictReader(handle)))
    write_csv(args.validation_output, queue)
    print(f"Campos por cultura: {len(rows)}; fila de revisão: {len(queue)}; decisões reaplicadas: {applied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
