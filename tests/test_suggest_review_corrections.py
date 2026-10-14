import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from suggest_review_corrections import suggestion_for_row


def test_suggestion_reads_explicit_value_from_excerpt():
    row = {
        "document_id": "doc", "document_path": "report.pdf", "candidate_pages": "1",
        "field_name": "expiration_date", "review_excerpt": "Validade do certificado: 31/03/2027",
    }
    assert suggestion_for_row(row) == ("31/03/2027", "prefilled_atomic_value_from_excerpt")
