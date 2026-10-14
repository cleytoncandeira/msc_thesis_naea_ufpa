import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.crop_area import apply_known_decisions, crop_area_consensus, crop_area_validation_queue


def candidate(field, value, page=1):
    return {"document_id": "doc", "document_path": "doc.pdf", "field_name": field, "value_raw": value, "value_normalized": value, "value_numeric": value, "page_number": page, "evidence_text": "evidence"}


def test_crop_area_keeps_soy_and_corn_separate():
    rows = crop_area_consensus([candidate("certified_soy_area_ha", "3900"), candidate("certified_corn_area_ha", "2048")])
    assert {row["field_name"] for row in rows} == {"certified_soy_area_ha", "certified_corn_area_ha"}
    assert all(row["consensus_status"] == "single_direct_crop_area_candidate" for row in rows)


def test_crop_area_marks_multiple_values_as_conflict_and_samples_it():
    rows = crop_area_consensus([candidate("certified_soy_area_ha", "3900", 1), candidate("certified_soy_area_ha", "4000", 2)])
    assert rows[0]["selected_value_raw"] == ""
    assert rows[0]["consensus_status"] == "needs_review_conflict"
    assert len(crop_area_validation_queue(rows, single_sample_size=0)) == 1


def test_known_human_decision_overrides_a_conflict_in_the_queue():
    queue = crop_area_validation_queue(crop_area_consensus([candidate("certified_soy_area_ha", "3900", 1), candidate("certified_soy_area_ha", "4000", 2)]), single_sample_size=0)
    applied = apply_known_decisions(queue, [{"document_id": "doc", "field_name": "certified_soy_area_ha", "human_decision": "correct", "corrected_value": "3900", "review_notes": "page 1"}])
    assert applied == 1
    assert queue[0]["corrected_value"] == "3900"
