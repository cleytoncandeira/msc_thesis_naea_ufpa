import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.consolidation import field_consensus


def candidate(value: str, page: int) -> dict:
    return {
        "document_id": "doc", "document_path": "report.pdf", "field_name": "certificate_code",
        "value_raw": value, "value_normalized": value, "value_numeric": "", "page_number": page,
        "source_extraction_method": "native_text", "evidence_text": "evidence",
    }


def test_consensus_keeps_repeated_single_value_unvalidated():
    row = field_consensus([candidate("RTRS-1", 1), candidate("RTRS-1", 2)])[0]
    assert row["consensus_status"] == "single_candidate_unvalidated"
    assert row["selected_value_raw"] == "RTRS-1"


def test_consensus_does_not_choose_among_conflicting_values():
    row = field_consensus([candidate("RTRS-1", 1), candidate("RTRS-2", 2)])[0]
    assert row["consensus_status"] == "needs_review_conflict"
    assert row["selected_value_raw"] == ""
