import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.review_migration import migrate_crop_review


def row(**kwargs):
    return {"document_id": "doc", "field_name": "certified_soy_area_ha", "selected_value_raw": "", "candidate_values": "", "human_decision": "", "corrected_value": "", "review_notes": ""} | kwargs


def test_migrates_equivalent_accept_and_correction():
    target = [row(selected_value_raw="62.554,20"), row(document_id="doc2", candidate_values="10 | 20")]
    previous = [row(selected_value_raw="62554.20", human_decision="accept"), row(document_id="doc2", candidate_values="20 | 10", human_decision="correct", corrected_value="20")]
    assert migrate_crop_review(previous, target) == 2
    assert [item["human_decision"] for item in target] == ["accept", "correct"]


def test_does_not_migrate_when_the_candidate_changed():
    target = [row(selected_value_raw="10")]
    previous = [row(selected_value_raw="20", human_decision="accept")]
    assert migrate_crop_review(previous, target) == 0
