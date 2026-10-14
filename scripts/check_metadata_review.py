"""Verifica a revisão humana e produz métricas por campo quando houver rótulos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.review import accuracy_summary, read_csv, review_completeness, review_issues, write_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Valida a revisão humana de metadados RTRS.")
    parser.add_argument("--review-file", type=Path, default=PROJECT_ROOT / "outputs/validation/metadata_human_validation.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/validation")
    args = parser.parse_args(argv)
    rows = read_csv(args.review_file)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    completeness = review_completeness(rows)
    issues = review_issues(rows)
    (args.output_dir / "metadata_review_progress.json").write_text(json.dumps(completeness, indent=2) + "\n", encoding="utf-8")
    metrics = accuracy_summary(rows)
    if metrics:
        write_csv(args.output_dir / "metadata_review_metrics.csv", metrics)
    if issues:
        write_csv(args.output_dir / "metadata_review_issues.csv", issues)
    print(json.dumps(completeness | {"semantic_issues": len(issues)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

