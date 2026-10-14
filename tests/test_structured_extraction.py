import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.structured_extraction import extract_metadata_from_page, normalize_number


def page(text: str) -> dict:
    return {"document_id": "doc", "document_path": "report.pdf", "page_number": 1, "text": text, "extraction_method": "native_text"}


def test_extracts_certificate_and_audit_date_with_evidence():
    records = extract_metadata_from_page(page("Código do certificado: RTRS-CUC-AGR-COC-0071\nData da auditoria: 23/06/2025"))
    values = {(record.field_name, record.value_raw) for record in records}
    assert ("certificate_code", "RTRS-CUC-AGR-COC-0071") in values
    assert ("audit_date", "23/06/2025") in values
    assert all(record.validation_status == "candidate_not_validated" for record in records)


def test_number_normalization_refuses_multiple_numbers():
    assert normalize_number("293.756,52") == "293756.52"
    assert normalize_number("Soja 293.756,52 / Milho 281.317,24") is None
    assert normalize_number("122765,2") == "122765.2"
    assert normalize_number("62554.20") == "62554.2"


def test_area_labels_are_kept_semantically_separate():
    records = extract_metadata_from_page(page("Área total (ha): 100\nÁrea cultivada (ha): 60\nÁrea certificada (ha): 40"))
    assert {record.field_name for record in records} == {"total_area_ha", "cultivated_area_ha", "certified_area_ha"}


def test_crop_areas_are_extracted_in_separate_fields():
    records = extract_metadata_from_page(page(
        "Área de soja a ser certificada (ha): Soja: 3.900,00 ha\nMilho: 2.048,00 ha\n"
        "Área cultivada SOJA(ha): 2.764,63\nÁrea cultivada MILHO(ha): 2.680,00"
    ))
    values = {(record.field_name, record.value_raw, record.value_numeric) for record in records}
    assert ("certified_soy_area_ha", "3.900,00", "3900") in values
    assert ("certified_corn_area_ha", "2.048,00", "2048") in values
    assert ("cultivated_soy_area_ha", "2.764,63", "2764.63") in values
    assert ("cultivated_corn_area_ha", "2.680,00", "2680") in values
