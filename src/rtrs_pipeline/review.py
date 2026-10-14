"""Validação de revisões humanas para a extração documental RTRS."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


VALID_DECISIONS = {"accept", "reject", "correct", "ambiguous"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def review_completeness(rows: list[dict[str, str]]) -> dict[str, int]:
    decisions = Counter((row.get("human_decision") or "").strip().casefold() for row in rows)
    invalid = set(decisions) - VALID_DECISIONS - {""}
    if invalid:
        raise ValueError(f"Decisões inválidas: {sorted(invalid)}")
    return {
        "total": len(rows),
        "completed": sum(decisions[decision] for decision in VALID_DECISIONS),
        "pending": decisions[""],
        **{decision: decisions[decision] for decision in sorted(VALID_DECISIONS)},
    }


def review_issues(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Sinaliza decisões formalmente preenchidas, porém semanticamente incompletas."""

    issues = []
    for index, row in enumerate(rows, start=2):
        decision = (row.get("human_decision") or "").strip().casefold()
        reason = ""
        if decision == "accept" and not (row.get("selected_value_raw") or "").strip():
            reason = "accept_requires_selected_value_raw"
        elif decision == "correct" and not (row.get("corrected_value") or "").strip():
            reason = "correct_requires_corrected_value"
        if reason:
            issues.append(
                {
                    "source_row": str(index),
                    "field_name": row.get("field_name", ""),
                    "document_path": row.get("document_path", ""),
                    "human_decision": decision,
                    "selected_value_raw": row.get("selected_value_raw", ""),
                    "corrected_value": row.get("corrected_value", ""),
                    "issue": reason,
                    "review_excerpt": row.get("review_excerpt", ""),
                }
            )
    return issues


def is_semantically_complete(row: dict[str, str]) -> bool:
    """Retorna se uma decisão possui os valores exigidos para ser mensurável."""

    decision = (row.get("human_decision") or "").strip().casefold()
    if decision == "accept":
        return bool((row.get("selected_value_raw") or "").strip())
    if decision == "correct":
        return bool((row.get("corrected_value") or "").strip())
    return bool(decision)


def normalize_explicit_corrections(rows: list[dict[str, str]]) -> int:
    """Converte em ``correct`` somente linhas com valor corrigido explicitamente preenchido."""

    changed = 0
    for row in rows:
        decision = (row.get("human_decision") or "").strip().casefold()
        corrected = (row.get("corrected_value") or "").strip()
        selected = (row.get("selected_value_raw") or "").strip()
        if corrected and (not decision or (decision == "accept" and not selected)):
            row["human_decision"] = "correct"
            row["review_notes"] = (row.get("review_notes") or "") + " [normalized_explicit_corrected_value]"
            changed += 1
    return changed


def accuracy_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    """Calcula aceitação por campo apenas sobre decisões humanas concluídas."""

    by_field: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        decision = (row.get("human_decision") or "").strip().casefold()
        if is_semantically_complete(row):
            by_field[row["field_name"]][decision] += 1
    summary = []
    for field_name, counts in sorted(by_field.items()):
        reviewed = sum(counts.values())
        correct = counts["accept"] + counts["correct"]
        summary.append(
            {
                "field_name": field_name,
                "reviewed": reviewed,
                "accept": counts["accept"],
                "correct": counts["correct"],
                "reject": counts["reject"],
                "ambiguous": counts["ambiguous"],
                "usable_rate": round(correct / reviewed, 4) if reviewed else "",
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

