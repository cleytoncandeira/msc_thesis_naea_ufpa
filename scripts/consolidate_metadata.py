"""Fase 3: consolida candidatos e prepara revisão humana."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import field_consensus, read_jsonl, validation_sample, write_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consolida candidatos de metadados RTRS sem validar valores.")
    parser.add_argument("--candidates", type=Path, default=PROJECT_ROOT / "outputs/tables/metadata_candidates.jsonl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/tables")
    parser.add_argument("--validation-dir", type=Path, default=PROJECT_ROOT / "outputs/validation")
    parser.add_argument("--sample-size", type=int, default=120)
    args = parser.parse_args(argv)
    summaries = field_consensus(list(read_jsonl(args.candidates)))
    write_csv(args.output_dir / "metadata_field_consensus.csv", summaries)
    sampled = validation_sample(summaries, args.validation_dir / "metadata_human_validation.csv", size=args.sample_size)
    print(f"Campos consolidados: {len(summaries)}; amostra de revisão: {sampled}")
    print(dict(Counter(row["consensus_status"] for row in summaries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
