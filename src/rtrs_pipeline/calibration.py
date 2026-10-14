"""Promoção conservadora de metadados a partir de uma revisão humana calibrada."""

from __future__ import annotations

from collections import Counter, defaultdict


AREA_FIELDS = {"certified_area_ha", "cultivated_area_ha", "total_area_ha"}
HARDBLOCKED_FIELDS = AREA_FIELDS | {"auditor"}
SINGLE_CANDIDATE_STATUSES = {"single_candidate_unvalidated", "single_direct_crop_area_candidate"}


def _decision(row: dict) -> str:
    return (row.get("human_decision") or "").strip().casefold()


def _usable(row: dict) -> bool:
    return _decision(row) == "accept" and bool((row.get("selected_value_raw") or "").strip()) or (
        _decision(row) == "correct" and bool((row.get("corrected_value") or "").strip())
    )


def calibrated_policies(review_rows: list[dict], *, min_reviewed: int = 5, min_usable_rate: float = 0.8) -> dict[tuple[str, str], dict]:
    """Define políticas automáticas somente para estratos suficientemente validados."""

    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for row in review_rows:
        # Uma linha ainda sem decisão não é evidência contra nem a favor da regra.
        if not _decision(row):
            continue
        key = (row["field_name"], row["consensus_status"])
        counts[key]["reviewed"] += 1
        counts[key]["usable"] += int(_usable(row))
    policies = {}
    for key, count in counts.items():
        field, status = key
        reviewed = count["reviewed"]
        rate = count["usable"] / reviewed if reviewed else 0.0
        enabled = (
            status in SINGLE_CANDIDATE_STATUSES
            and field not in HARDBLOCKED_FIELDS
            and reviewed >= min_reviewed
            and rate >= min_usable_rate
        )
        policies[key] = {
            "field_name": field,
            "consensus_status": status,
            "reviewed": reviewed,
            "usable": count["usable"],
            "usable_rate": round(rate, 4),
            "auto_promotion_enabled": str(enabled).lower(),
            "reason": "eligible_calibrated_single_candidate" if enabled else "insufficient_or_unsafe_calibration",
        }
    return policies


def promote_metadata(consensus_rows: list[dict], review_rows: list[dict], policies: dict[tuple[str, str], dict]) -> tuple[list[dict], list[dict]]:
    """Promove decisões humanas e candidatos únicos calibrados; explica cada retenção."""

    promoted: list[dict] = []
    withheld: list[dict] = []
    reviewed = {(row["document_id"], row["field_name"]): row for row in review_rows}

    for row in consensus_rows:
        key = (row["document_id"], row["field_name"])
        review = reviewed.get(key)
        field = row["field_name"]
        if review:
            decision = _decision(review)
            if field in AREA_FIELDS:
                withheld.append(row | {"promotion_reason": "legacy_area_review_not_promoted_after_area_semantics_change", "human_decision": decision})
                continue
            if _usable(review):
                value = review["corrected_value"].strip() if decision == "correct" else review["selected_value_raw"].strip()
                promoted.append(row | {
                    "selected_value_raw": value,
                    "selected_value_normalized": value,
                    "selected_value_numeric": "",
                    "promotion_status": "human_validated_corrected" if decision == "correct" else "human_validated_accepted",
                    "human_decision": decision,
                })
            else:
                withheld.append(row | {"promotion_reason": f"human_{decision or 'incomplete'}", "human_decision": decision})
            continue

        policy = policies.get((field, row["consensus_status"]))
        if policy and policy["auto_promotion_enabled"] == "true":
            promoted.append(row | {"promotion_status": "auto_promoted_calibrated_single_candidate", "human_decision": ""})
        else:
            reason = "no_calibration_for_stratum"
            if field in AREA_FIELDS:
                reason = "area_requires_area_v2_review"
            elif field in HARDBLOCKED_FIELDS:
                reason = "field_blocked_by_calibration"
            elif row["consensus_status"] == "needs_review_conflict":
                reason = "unreviewed_conflict"
            withheld.append(row | {"promotion_reason": reason, "human_decision": ""})
    return promoted, withheld
