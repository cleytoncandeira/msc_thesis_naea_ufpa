import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.analysis_table import pivot_research_rows
from rtrs_pipeline.consolidation import write_csv


def source(doc, field, value, numeric=""):
    return {"document_id": doc, "document_path": f"{doc}.pdf", "field_name": field, "value_normalized": value, "value_numeric": numeric, "promotion_status": "human_validated_accepted"}


def test_pivot_creates_one_document_row_and_numeric_column():
    rows, coverage = pivot_research_rows([source("a", "enterprise_name", "Farm"), source("a", "certified_soy_area_ha", "100", "100")])
    assert rows == [{"document_id": "a", "document_path": "a.pdf", "enterprise_name": "Farm", "enterprise_name__provenance": "human_validated_accepted", "certified_soy_area_ha": "100", "certified_soy_area_ha__numeric": "100", "certified_soy_area_ha__provenance": "human_validated_accepted"}]
    assert {item["field_name"] for item in coverage} == {"enterprise_name", "certified_soy_area_ha"}


def test_pivot_rejects_duplicate_document_field():
    with pytest.raises(ValueError):
        pivot_research_rows([source("a", "enterprise_name", "A"), source("a", "enterprise_name", "B")])


def test_write_csv_keeps_columns_present_only_in_later_rows(tmp_path):
    output = tmp_path / "wide.csv"
    write_csv(output, [{"document_id": "a", "field_a": "1"}, {"document_id": "b", "field_b": "2"}])
    assert output.read_text(encoding="utf-8").splitlines()[0] == "document_id,field_a,field_b"
