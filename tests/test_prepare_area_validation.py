import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from prepare_area_validation import prepare_area_validation


def row(field, value, page=1):
    return {"document_id": "doc", "document_path": "doc.pdf", "field_name": field, "value_raw": value, "value_normalized": value, "value_numeric": value, "page_number": page, "evidence_text": f"{field}: {value}"}


def test_cultivated_is_explicit_fallback_and_total_is_context_only():
    queue = prepare_area_validation([row("cultivated_area_ha", "20"), row("total_area_ha", "100")])
    assert queue[0]["selected_value_raw"] == "20"
    assert queue[0]["suggested_area_source"] == "cultivated_area_ha"
    assert queue[0]["total_area_candidates_context_only"] == "100"


def test_total_never_becomes_selected_area():
    queue = prepare_area_validation([row("total_area_ha", "100")])
    assert queue[0]["selected_value_raw"] == ""
    assert queue[0]["suggested_area_source"] == ""
