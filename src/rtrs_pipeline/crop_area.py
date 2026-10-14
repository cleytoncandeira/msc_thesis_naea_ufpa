"""Consolida áreas de soja e milho sem fundir culturas ou safras."""

from __future__ import annotations

import random
from collections import defaultdict


CROP_AREA_FIELDS = {
    "certified_soy_area_ha",
    "certified_corn_area_ha",
    "cultivated_soy_area_ha",
    "cultivated_corn_area_ha",
}


def crop_area_consensus(candidates: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in candidates:
        if row["field_name"] in CROP_AREA_FIELDS:
            grouped[(row["document_id"], row["field_name"])].append(row)
    output = []
    for (document_id, field), rows in sorted(grouped.items()):
        values: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            values[row["value_normalized"]].append(row)
        ranked = sorted(values.items(), key=lambda pair: (-len(pair[1]), pair[0]))
        value, selected = ranked[0]
        representative = selected[0]
        conflict = len(ranked) > 1
        output.append({
            "document_id": document_id,
            "document_path": representative["document_path"],
            "field_name": field,
            "selected_value_raw": "" if conflict else representative["value_raw"],
            "selected_value_numeric": "" if conflict else representative.get("value_numeric", ""),
            "candidate_values": " | ".join(value for value, _ in ranked),
            "candidate_pages": "|".join(str(row["page_number"]) for _, items in ranked for row in items),
            "candidate_count": len(rows),
            "consensus_status": "needs_review_conflict" if conflict else "single_direct_crop_area_candidate",
            "review_excerpt": representative["evidence_text"],
        })
    return output


def crop_area_validation_queue(rows: list[dict], *, single_sample_size: int = 30, seed: int = 2026) -> list[dict]:
    """Inclui todos os conflitos e uma amostra reprodutível de candidatos diretos."""

    conflicts = [row for row in rows if row["consensus_status"] == "needs_review_conflict"]
    singles = [row for row in rows if row["consensus_status"] == "single_direct_crop_area_candidate"]
    rng = random.Random(seed)
    sampled = rng.sample(singles, min(single_sample_size, len(singles)))
    queue = conflicts + sampled
    queue.sort(key=lambda row: (row["document_path"], row["field_name"]))
    return [row | {"human_decision": "", "corrected_value": "", "reviewer": "", "review_notes": ""} for row in queue]


def apply_known_decisions(queue: list[dict], decisions: list[dict]) -> int:
    """Reaplica decisões humanas já registradas por documento e campo."""

    lookup = {(row["document_id"], row["field_name"]): row for row in decisions}
    applied = 0
    for row in queue:
        decision = lookup.get((row["document_id"], row["field_name"]))
        if decision:
            for field in ("human_decision", "selected_value_raw", "corrected_value", "reviewer", "review_notes"):
                if field in decision:
                    row[field] = decision[field]
            applied += 1
    return applied
