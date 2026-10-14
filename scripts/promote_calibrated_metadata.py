"""Promove metadados RTRS somente quando a revisão humana sustenta a regra."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.calibration import calibrated_policies, promote_metadata
from rtrs_pipeline.review import read_csv, write_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promove candidatos calibrados por revisão humana.")
    parser.add_argument("--consensus", type=Path, default=PROJECT_ROOT / "outputs/tables/metadata_field_consensus.csv")
    parser.add_argument("--review", type=Path, default=PROJECT_ROOT / "outputs/validation/metadata_human_validation_resolved.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/tables/calibrated")
    args = parser.parse_args(argv)
    consensus = read_csv(args.consensus)
    review = read_csv(args.review)
    policies = calibrated_policies(review)
    promoted, withheld = promote_metadata(consensus, review, policies)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "metadata_calibration_policy.csv", list(policies.values()))
    write_csv(args.output_dir / "metadata_promoted_calibrated.csv", promoted)
    write_csv(args.output_dir / "metadata_withheld_for_review.csv", withheld)
    print(f"Promovidos: {len(promoted)}; retidos: {len(withheld)}; políticas: {len(policies)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
