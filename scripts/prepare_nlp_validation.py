"""CLI inicial para Fase 4: recuperação da saída LLaMA e amostra humana."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.nlp_protocol import make_validation_rows, summarize_legacy_pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fase 4: preparação da validação de PLN.")
    parser.add_argument("--llama-csv", type=Path, default=PROJECT_ROOT / "data/processed_data/llama2_result.csv")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/validation")
    parser.add_argument("--sample-size", type=int, default=80)
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_legacy_pairs(args.llama_csv)
    (args.output_dir / "legacy_pair_summary.txt").write_text(
        "\n".join(f"{label},{count}" for label, count in sorted(summary.items())) + "\n", encoding="utf-8"
    )
    count = make_validation_rows(args.llama_csv, args.output_dir / "historical_llama_human_validation.csv", sample_size=args.sample_size)
    print(f"Amostra de validação criada: {count} linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

