import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.calibration import calibrated_policies, promote_metadata


def review(field, status, decision="accept", selected="value", corrected=""):
    return {"document_id": "reviewed", "field_name": field, "consensus_status": status, "human_decision": decision, "selected_value_raw": selected, "corrected_value": corrected}


def consensus(doc, field, status="single_candidate_unvalidated", value="value"):
    return {"document_id": doc, "document_path": f"{doc}.pdf", "field_name": field, "consensus_status": status, "selected_value_raw": value, "selected_value_normalized": value, "selected_value_numeric": ""}


def test_policy_enables_only_well_sampled_single_candidate_fields():
    rows = [review("enterprise_name", "single_candidate_unvalidated") for _ in range(5)]
    rows += [review("auditor", "single_candidate_unvalidated") for _ in range(5)]
    policies = calibrated_policies(rows)
    assert policies[("enterprise_name", "single_candidate_unvalidated")]["auto_promotion_enabled"] == "true"
    assert policies[("auditor", "single_candidate_unvalidated")]["auto_promotion_enabled"] == "false"


def test_policy_excludes_pending_rows_from_calibration_denominator():
    rows = [review("enterprise_name", "single_candidate_unvalidated") for _ in range(5)]
    rows += [review("enterprise_name", "single_candidate_unvalidated", decision="", selected="") for _ in range(20)]
    policies = calibrated_policies(rows)
    assert policies[("enterprise_name", "single_candidate_unvalidated")]["reviewed"] == 5
    assert policies[("enterprise_name", "single_candidate_unvalidated")]["usable_rate"] == 1.0


def test_policy_recognizes_a_direct_crop_candidate_as_single_candidate():
    rows = [review("certified_soy_area_ha", "single_direct_crop_area_candidate") for _ in range(5)]
    policies = calibrated_policies(rows)
    assert policies[("certified_soy_area_ha", "single_direct_crop_area_candidate")]["auto_promotion_enabled"] == "true"


def test_promotion_uses_human_correction_and_withholds_area():
    reviews = [review("enterprise_name", "single_candidate_unvalidated", "correct", "wrong", "right")]
    policies = calibrated_policies(reviews, min_reviewed=1)
    promoted, withheld = promote_metadata(
        [consensus("reviewed", "enterprise_name", value="wrong"), consensus("area", "certified_area_ha", value="10")],
        reviews,
        policies,
    )
    assert promoted[0]["selected_value_raw"] == "right"
    assert promoted[0]["promotion_status"] == "human_validated_corrected"
    assert withheld[0]["promotion_reason"] == "area_requires_area_v2_review"
