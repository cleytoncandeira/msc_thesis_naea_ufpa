import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.review import accuracy_summary, normalize_explicit_corrections, review_completeness, review_issues


def test_review_completeness_counts_valid_decisions():
    rows = [{"human_decision": "accept"}, {"human_decision": ""}, {"human_decision": "correct"}]
    assert review_completeness(rows)["completed"] == 2
    assert review_completeness(rows)["pending"] == 1


def test_review_completeness_rejects_unknown_decision():
    with pytest.raises(ValueError):
        review_completeness([{"human_decision": "maybe"}])


def test_accuracy_summary_uses_only_reviewed_rows():
    rows = [
        {"field_name": "audit_date", "human_decision": "accept", "selected_value_raw": "2021-01-01"},
        {"field_name": "audit_date", "human_decision": "reject"},
        {"field_name": "audit_date", "human_decision": ""},
    ]
    assert accuracy_summary(rows) == [{"field_name": "audit_date", "reviewed": 2, "accept": 1, "correct": 0, "reject": 1, "ambiguous": 0, "usable_rate": 0.5}]


def test_review_issues_detects_missing_values_for_accept_and_correct():
    rows = [
        {"human_decision": "accept", "selected_value_raw": "", "corrected_value": ""},
        {"human_decision": "correct", "selected_value_raw": "", "corrected_value": ""},
        {"human_decision": "reject", "selected_value_raw": "", "corrected_value": ""},
    ]
    assert [issue["issue"] for issue in review_issues(rows)] == ["accept_requires_selected_value_raw", "correct_requires_corrected_value"]


def test_accuracy_summary_excludes_semantically_incomplete_decisions():
    rows = [
        {"field_name": "certificate", "human_decision": "accept", "selected_value_raw": ""},
        {"field_name": "certificate", "human_decision": "correct", "corrected_value": "RTRS-1"},
    ]
    assert accuracy_summary(rows) == [{"field_name": "certificate", "reviewed": 1, "accept": 0, "correct": 1, "reject": 0, "ambiguous": 0, "usable_rate": 1.0}]


def test_normalize_explicit_corrections_only_when_a_value_was_supplied():
    rows = [
        {"human_decision": "", "selected_value_raw": "", "corrected_value": "42", "review_notes": ""},
        {"human_decision": "accept", "selected_value_raw": "", "corrected_value": "43", "review_notes": ""},
        {"human_decision": "accept", "selected_value_raw": "44", "corrected_value": "45", "review_notes": ""},
    ]
    assert normalize_explicit_corrections(rows) == 2
    assert [row["human_decision"] for row in rows] == ["correct", "correct", "accept"]
