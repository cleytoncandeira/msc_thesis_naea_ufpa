"""Prepara revisão humana específica para a semântica de área RTRS."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import write_csv


AREA_FIELDS = ("certified_area_ha", "cultivated_area_ha", "total_area_ha")


def distinct(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output = []
    for row in rows:
        value = (row.get("value_normalized") or "").strip()
        if value and value not in seen:
            seen.add(value)
            output.append(row)
    return output


def prepare_area_validation(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    """Uma linha por documento; área total é contexto, nunca sugestão de fallback."""

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        if row["field_name"] in AREA_FIELDS:
            grouped[row["document_id"]].append(row)
    queue = []
    for document_id, rows in sorted(grouped.items()):
        by_field = {field: distinct([row for row in rows if row["field_name"] == field]) for field in AREA_FIELDS}
        selected = (by_field["certified_area_ha"] or by_field["cultivated_area_ha"] or [None])[0]
        source = "certified_area_ha" if by_field["certified_area_ha"] else "cultivated_area_ha" if by_field["cultivated_area_ha"] else ""
        context = selected or (by_field["total_area_ha"] or [None])[0] or rows[0]
        def values(field: str) -> str:
            return " | ".join(row["value_raw"] for row in by_field[field])
        queue.append(
            {
                "document_id": document_id,
                "document_path": context["document_path"],
                "field_name": "analysis_area_ha",
                "selected_value_raw": selected["value_raw"] if selected else "",
                "selected_value_numeric": selected.get("value_numeric", "") if selected else "",
                "suggested_area_source": source,
                "certified_area_candidates": values("certified_area_ha"),
                "cultivated_area_candidates": values("cultivated_area_ha"),
                "total_area_candidates_context_only": values("total_area_ha"),
                "candidate_pages": "|".join(str(row["page_number"]) for row in (by_field["certified_area_ha"] or by_field["cultivated_area_ha"] or by_field["total_area_ha"])),
                "review_excerpt": context["evidence_text"],
                "human_decision": "",
                "corrected_value": "",
                "reviewer": "",
                "review_notes": "",
            }
        )
    return queue


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera fila de validação de áreas RTRS.")
    parser.add_argument("--candidates", type=Path, default=PROJECT_ROOT / "outputs/tables/metadata_candidates_area_v2.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/validation/area_semantics_human_validation.csv")
    args = parser.parse_args(argv)
    with args.candidates.open(encoding="utf-8", newline="") as handle:
        queue = prepare_area_validation(list(csv.DictReader(handle)))
    write_csv(args.output, queue)
    print(f"Linhas para revisão de área: {len(queue)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
