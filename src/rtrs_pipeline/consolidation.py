"""Consolidação conservadora de candidatos estruturados, sem validação implícita."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterator


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def canonical_value(row: dict) -> str:
    return row.get("value_numeric") or " ".join(row["value_normalized"].casefold().split())


def field_consensus(candidates: list[dict]) -> list[dict]:
    """Resume valores por documento/campo; conflito sempre exige revisão."""

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for candidate in candidates:
        grouped[(candidate["document_id"], candidate["field_name"])].append(candidate)
    summaries = []
    for (document_id, field_name), rows in sorted(grouped.items()):
        variants: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            variants[canonical_value(row)].append(row)
        values = sorted(variants.items(), key=lambda item: (-len(item[1]), item[0]))
        _, selected_rows = values[0]
        representative = selected_rows[0]
        status = "single_candidate_unvalidated" if len(values) == 1 else "needs_review_conflict"
        summaries.append(
            {
                "document_id": document_id,
                "document_path": representative["document_path"],
                "field_name": field_name,
                "selected_value_raw": representative["value_raw"] if status == "single_candidate_unvalidated" else "",
                "selected_value_normalized": representative["value_normalized"] if status == "single_candidate_unvalidated" else "",
                "selected_value_numeric": representative.get("value_numeric", "") if status == "single_candidate_unvalidated" else "",
                "distinct_candidate_values": len(values),
                "candidate_occurrences": len(rows),
                "candidate_pages": "|".join(str(row["page_number"]) for row in selected_rows),
                "source_methods": "|".join(sorted({row["source_extraction_method"] for row in rows})),
                "consensus_status": status,
                "review_excerpt": representative["evidence_text"],
            }
        )
    return summaries


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Tabelas largas podem ter campos ausentes em parte dos documentos.
    # Mantemos a ordem da primeira ocorrência e nunca descartamos colunas tardias.
    fields = list(dict.fromkeys(field for row in rows for field in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validation_sample(summaries: list[dict], output_path: Path, *, size: int = 120, seed: int = 2026) -> int:
    """Amostra determinística, equilibrando conflito e candidato único."""

    rng = random.Random(seed)
    conflicts = [row for row in summaries if row["consensus_status"] == "needs_review_conflict"]
    singles = [row for row in summaries if row["consensus_status"] == "single_candidate_unvalidated"]
    target_conflicts = min(len(conflicts), size // 2)
    target_singles = min(len(singles), size - target_conflicts)
    sample = rng.sample(conflicts, target_conflicts) + rng.sample(singles, target_singles)
    rng.shuffle(sample)
    review_rows = [row | {"human_decision": "", "corrected_value": "", "reviewer": "", "review_notes": ""} for row in sample]
    write_csv(output_path, review_rows)
    return len(review_rows)
