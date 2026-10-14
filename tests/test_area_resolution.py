import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.area_resolution import resolve_area


def row(field: str, value: str) -> dict[str, str]:
    return {"document_id": "doc", "document_path": "report.pdf", "field_name": field, "value_raw": value, "value_numeric": value}


def test_certified_area_has_priority_over_cultivated_and_total():
    result = resolve_area([row("total_area_ha", "100"), row("cultivated_area_ha", "60"), row("certified_area_ha", "40")])[0]
    assert result["analysis_area_numeric"] == "40"
    assert result["analysis_area_source"] == "certified_area_ha"


def test_cultivated_is_explicit_fallback_not_total():
    result = resolve_area([row("total_area_ha", "100"), row("cultivated_area_ha", "60")])[0]
    assert result["analysis_area_numeric"] == "60"
    assert result["resolution_status"] == "fallback_cultivated_area_candidate"
