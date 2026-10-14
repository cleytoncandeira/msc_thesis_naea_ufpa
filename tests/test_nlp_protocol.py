import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.nlp_protocol import aggregate_validated_labels, parse_legacy_pairs


def test_parse_legacy_pairs_does_not_interpret_free_text():
    pairs = parse_legacy_pairs("Resposta: ['legal compliance', 'yes'] e ['bribery', 'no']")
    assert pairs == [{"feature": "legal compliance", "legacy_label": "yes"}, {"feature": "bribery", "legacy_label": "no"}]


def test_aggregate_validated_labels_counts_five_categories():
    totals = aggregate_validated_labels([{"human_label": "favorable"}, {"human_label": "ambiguous"}])
    assert totals == {"favorable": 1, "contrary": 0, "insufficient": 0, "not_applicable": 0, "ambiguous": 1}


def test_aggregate_validated_labels_rejects_unknown_category():
    with pytest.raises(ValueError):
        aggregate_validated_labels([{"human_label": "positive"}])
