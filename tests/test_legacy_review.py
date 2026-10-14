import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.legacy_review import legacy_linkage_review_queue


def test_queue_groups_multiple_candidates_into_one_decision_row():
    register = [{"document_id": "doc", "document_path": "doc.pdf", "enterprise_name": "Farm", "legacy_match_status": "candidate_entity_match_requires_review", "audit_date": "2024", "issue_date": "", "expiration_date": ""}]
    candidates = [
        {"document_id": "doc", "legacy_record_id": "2", "legacy_organization": "Farm", "legacy_name": "Farm", "legacy_year": "2023", "legacy_regtag": "R-2", "legacy_links": "two", "match_score": "100", "year_match": "false"},
        {"document_id": "doc", "legacy_record_id": "1", "legacy_organization": "Farm", "legacy_name": "Farm", "legacy_year": "2024", "legacy_regtag": "R-1", "legacy_links": "one", "match_score": "140", "year_match": "true"},
    ]
    queue = legacy_linkage_review_queue(register, candidates)
    assert len(queue) == 1
    assert queue[0]["proposed_legacy_record_id"] == "1"
    assert "id=2" in queue[0]["candidate_options"]
    assert queue[0]["proposed_certificate_code"] == "R-1"
