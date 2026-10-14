import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.farm_linkage import document_farm_rows


def test_document_farm_linkage_keeps_one_to_many_structure():
    register = [{"document_id": "doc", "document_path": "doc.pdf", "legacy_record_id": "0", "legacy_match_status": "linked_exact_name_certificate_year", "legacy_Organization": "Grupo Arvore", "legacy_Name": "Grupo Arvore"}]
    farms = [
        {"Organization": "Grupo Arvore", "Name": "Grupo Arvore", "Farm": "A", "Latitude": "-1", "Longitude": "-2", "State": "PA", "City": "X"},
        {"Organization": "Grupo Arvore", "Name": "Grupo Arvore", "Farm": "B", "Latitude": "-3", "Longitude": "-4", "State": "PA", "City": "Y"},
    ]
    assert [row["farm"] for row in document_farm_rows(register, farms)] == ["A", "B"]
