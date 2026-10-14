"""Resolve a origem da área para análise sem apagar medidas alternativas."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


AREA_FIELDS = ("certified_area_ha", "cultivated_area_ha", "total_area_ha")


def read_candidates(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["field_name"] in AREA_FIELDS]


def resolve_area(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    """Prioriza rótulo certificado; usa cultivada somente como fallback explícito."""

    grouped: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in candidates:
        grouped[row["document_id"]][row["field_name"]].append(row)
    output = []
    for document_id, by_field in sorted(grouped.items()):
        source = by_field.get("certified_area_ha") or by_field.get("cultivated_area_ha") or []
        if by_field.get("certified_area_ha"):
            status = "direct_certified_area_candidate"
        elif by_field.get("cultivated_area_ha"):
            status = "fallback_cultivated_area_candidate"
        else:
            status = "no_certified_or_cultivated_area_candidate"
        representative = (source or by_field.get("total_area_ha") or [{}])[0]
        output.append(
            {
                "document_id": document_id,
                "document_path": representative.get("document_path", ""),
                "analysis_area_raw": representative.get("value_raw", "") if source else "",
                "analysis_area_numeric": representative.get("value_numeric", "") if source else "",
                "analysis_area_source": "certified_area_ha" if status.startswith("direct") else "cultivated_area_ha" if status.startswith("fallback") else "",
                "resolution_status": status,
                "total_area_candidate_count": len(by_field.get("total_area_ha", [])),
                "certified_area_candidate_count": len(by_field.get("certified_area_ha", [])),
                "cultivated_area_candidate_count": len(by_field.get("cultivated_area_ha", [])),
                "validation_status": "candidate_not_validated",
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        fields = list(rows[0]) if rows else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
