import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.legacy_linkage import link_legacy_rows


def doc(name, date):
    return {"document_id": "doc", "document_path": "doc.pdf", "enterprise_name": name, "issue_date": date, "audit_date": "", "expiration_date": ""}


def legacy(name, year):
    return {"Organization": name, "Name": name, "Year": year, "RegTag": "", "1_1_criteria": "criterion"}


def test_links_only_exact_entity_and_year_with_unique_best():
    register, candidates = link_legacy_rows([doc("Fazenda Árvore Ltda.", "10/01/2024")], [legacy("Fazenda Arvore", "2024"), legacy("Fazenda Arvore", "2023")])
    assert register[0]["legacy_match_status"] == "linked_exact_entity_and_year_code_unavailable"
    assert register[0]["legacy_1_1_criteria"] == "criterion"
    assert len(candidates) == 2


def test_leaves_entity_match_without_year_as_review_candidate():
    register, _ = link_legacy_rows([doc("Fazenda Arvore", "10/01/2024")], [legacy("Fazenda Arvore", "2023")])
    assert register[0]["legacy_match_status"] == "candidate_entity_match_requires_review"
    assert not register[0]["legacy_record_id"]


def test_name_certificate_and_year_create_confirmed_identity_link():
    document = doc("Fazenda Arvore", "10/01/2024") | {"certificate_code": "RTRS-CUC-001"}
    historic = legacy("Fazenda Arvore", "2024") | {"RegTag": "RTRS CUC 001"}
    register, _ = link_legacy_rows([document], [historic])
    assert register[0]["legacy_match_status"] == "linked_exact_name_certificate_year"


def test_divergent_available_certificate_stays_for_review():
    document = doc("Fazenda Arvore", "10/01/2024") | {"certificate_code": "RTRS-CUC-001"}
    historic = legacy("Fazenda Arvore", "2024") | {"RegTag": "RTRS CUC 999"}
    register, _ = link_legacy_rows([document], [historic])
    assert register[0]["legacy_match_status"] == "candidate_entity_match_requires_review"
