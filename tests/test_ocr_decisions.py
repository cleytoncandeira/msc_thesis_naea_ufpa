import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def test_ocr_decision_file_has_only_documented_decisions():
    path = PROJECT_ROOT / "outputs/intermediate/ocr_review_decisions.csv"
    if not path.exists():
        return
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {row["decision"] for row in rows} <= {"ocr_approved", "skip_blank"}
    assert all(row["decision_reason"] for row in rows)
