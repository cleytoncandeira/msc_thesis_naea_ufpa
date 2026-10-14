"""Gera uma revisão de área v4 com decisões equivalentes migradas da v3."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.review import read_csv, write_csv
from rtrs_pipeline.review_migration import migrate_crop_review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migra revisão equivalente entre rodadas de área.")
    parser.add_argument("--previous", type=Path, default=PROJECT_ROOT / "outputs/validation/crop_area_human_validation_resolved.csv")
    parser.add_argument("--target", type=Path, default=PROJECT_ROOT / "outputs/validation/crop_area_human_validation_v4.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/validation/crop_area_human_validation_v4_migrated.csv")
    args = parser.parse_args(argv)
    target = read_csv(args.target)
    migrated = migrate_crop_review(read_csv(args.previous), target)
    write_csv(args.output, target)
    print(f"Decisões migradas: {migrated}; arquivo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
