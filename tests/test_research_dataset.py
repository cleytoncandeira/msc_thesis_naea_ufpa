import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.research_dataset import research_rows


def promoted(doc, field, value, **extra):
    return {"document_id": doc, "document_path": f"{doc}.pdf", "field_name": field, "selected_value_raw": value, "selected_value_normalized": value, "selected_value_numeric": "", "promotion_status": "human_validated_accepted", "human_decision": "accept"} | extra


def test_research_rows_combines_sources_and_normalizes_crop_area_number():
    rows = research_rows([promoted("one", "enterprise_name", "Farm")], [promoted("two", "certified_soy_area_ha", "62.554,20")])
    assert len(rows) == 2
    assert next(row for row in rows if row["field_name"] == "certified_soy_area_ha")["value_numeric"] == "62554.2"


def test_research_rows_rejects_duplicate_document_field():
    with pytest.raises(ValueError):
        research_rows([promoted("one", "enterprise_name", "A")], [promoted("one", "enterprise_name", "B")])
