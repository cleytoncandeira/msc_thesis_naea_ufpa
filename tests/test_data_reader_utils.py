from pathlib import Path

import pytest

from scripts.data_reader.annotation_tool import order_pages_by_index
from scripts.data_reader.ocr_dataset import bbox_center_in, compute_iou
from scripts.data_reader.report_organizer import identify_company
from scripts.data_reader.report_stats import count_reports_by_company, find_companies_below_threshold


def test_identify_company_matches_regex():
    text = "O relatório oficial da Food Chain ID confirma a certificação."
    assert identify_company(text) == "Food Chain ID"


def test_identify_company_returns_none_for_unknown():
    assert identify_company("Empresa desconhecida") is None


def test_count_reports_by_company(tmp_path: Path):
    control_union = tmp_path / "Control Union"
    control_union.mkdir()
    (control_union / "report_a").mkdir()
    (control_union / "report_b").mkdir()

    food_chain = tmp_path / "Food Chain ID"
    food_chain.mkdir()
    (food_chain / "report_1").mkdir()

    counts = count_reports_by_company(tmp_path)
    assert counts == {"Control Union": 2, "Food Chain ID": 1}


def test_find_companies_below_threshold():
    counts = {"Control Union": 4, "Food Chain ID": 2}
    assert find_companies_below_threshold(counts, minimum=3) == {"Food Chain ID": 2}


def test_order_pages_by_index_sorts_numerically(tmp_path: Path):
    files = []
    for name in ["page_10.jpg", "page_2.jpg", "page_1.jpg"]:
        path = tmp_path / name
        path.write_text("dummy")
        files.append(path)

    ordered = order_pages_by_index(files)
    assert [p.name for p in ordered] == ["page_1.jpg", "page_2.jpg", "page_10.jpg"]


@pytest.mark.parametrize(
    "token, field, expected",
    [([0, 0, 10, 10], [0, 0, 10, 10], 1.0), ([0, 0, 5, 5], [5, 5, 10, 10], 0.0)],
)
def test_compute_iou(token, field, expected):
    assert compute_iou(token, field) == pytest.approx(expected, rel=1e-3)


def test_bbox_center_in():
    assert bbox_center_in([0, 0, 10, 10], [0, 0, 20, 20]) is True
    assert bbox_center_in([30, 30, 40, 40], [0, 0, 20, 20]) is False
