"""Aplica decisões editadas na fila de pendências à planilha de revisão-fonte."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EDITABLE_COLUMNS = ("human_decision", "selected_value_raw", "corrected_value")


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def apply_updates(source_rows: list[dict[str, str]], issue_rows: list[dict[str, str]]) -> int:
    """Atualiza linhas por seu número CSV (inclui cabeçalho), com validação de campo."""

    applied = 0
    for issue in issue_rows:
        line = int(issue["source_row"])
        row_index = line - 2
        if row_index < 0 or row_index >= len(source_rows):
            raise ValueError(f"source_row fora da planilha-fonte: {line}")
        source = source_rows[row_index]
        if source.get("field_name") != issue.get("field_name") or source.get("document_path") != issue.get("document_path"):
            raise ValueError(f"A fila não corresponde à linha {line}; aplicação interrompida.")
        for column in EDITABLE_COLUMNS:
            source[column] = issue.get(column, "")
        source["review_notes"] = (source.get("review_notes") or "") + " [resolved_from_issue_queue]"
        applied += 1
    return applied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Aplica uma fila editada à revisão de metadados.")
    parser.add_argument("--source", type=Path, default=PROJECT_ROOT / "outputs/validation/metadata_human_validation_suggested.csv")
    parser.add_argument("--issue-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/validation/metadata_human_validation_resolved.csv")
    args = parser.parse_args(argv)

    source_rows, fields = read_rows(args.source)
    issue_rows, _ = read_rows(args.issue_file)
    applied = apply_updates(source_rows, issue_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(source_rows)
    print(f"Atualizações aplicadas: {applied}; arquivo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
