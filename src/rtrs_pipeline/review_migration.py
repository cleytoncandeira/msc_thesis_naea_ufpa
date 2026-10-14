"""Migra decisões entre rodadas somente quando os valores continuam equivalentes."""

from __future__ import annotations

from rtrs_pipeline.structured_extraction import normalize_number


def numeric(value: str) -> str:
    return normalize_number(value or "") or ""


def candidate_numbers(row: dict) -> tuple[str, ...]:
    return tuple(sorted(filter(None, (numeric(value) for value in (row.get("candidate_values") or "").split(" | ")))))


def migrate_crop_review(previous_rows: list[dict], target_rows: list[dict]) -> int:
    """Copia decisões apenas se valor/candidatos preservam a mesma interpretação."""

    previous = {(row["document_id"], row["field_name"]): row for row in previous_rows}
    migrated = 0
    for target in target_rows:
        old = previous.get((target["document_id"], target["field_name"]))
        if not old or not (old.get("human_decision") or "").strip():
            continue
        decision = old["human_decision"].strip().casefold()
        allowed = False
        if decision == "accept":
            allowed = numeric(old.get("selected_value_raw", "")) == numeric(target.get("selected_value_raw", "")) and bool(numeric(target.get("selected_value_raw", "")))
        elif decision == "correct":
            allowed = numeric(old.get("corrected_value", "")) in candidate_numbers(target)
        elif decision == "reject":
            allowed = candidate_numbers(old) == candidate_numbers(target)
        if not allowed:
            continue
        for field in ("human_decision", "selected_value_raw", "corrected_value", "reviewer", "review_notes"):
            target[field] = old.get(field, "")
        target["review_notes"] = (target.get("review_notes") or "") + " [migrated_equivalent_v3_review]"
        migrated += 1
    return migrated
