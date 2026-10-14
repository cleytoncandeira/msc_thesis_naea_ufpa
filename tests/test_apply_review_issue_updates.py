import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apply_review_issue_updates import apply_updates


def test_apply_updates_uses_source_row_and_preserves_other_rows():
    source = [
        {"field_name": "certificate_code", "document_path": "a.pdf", "human_decision": "correct", "selected_value_raw": "old", "corrected_value": "", "review_notes": ""},
        {"field_name": "audit_date", "document_path": "b.pdf", "human_decision": "reject", "selected_value_raw": "", "corrected_value": "", "review_notes": ""},
    ]
    queue = [{"source_row": "2", "field_name": "certificate_code", "document_path": "a.pdf", "human_decision": "accept", "selected_value_raw": "RTRS-1", "corrected_value": ""}]
    assert apply_updates(source, queue) == 1
    assert source[0]["human_decision"] == "accept"
    assert source[0]["selected_value_raw"] == "RTRS-1"
    assert source[1]["human_decision"] == "reject"


def test_apply_updates_rejects_mismatched_queue_row():
    with pytest.raises(ValueError):
        apply_updates(
            [{"field_name": "audit_date", "document_path": "a.pdf"}],
            [{"source_row": "2", "field_name": "certificate_code", "document_path": "a.pdf"}],
        )
