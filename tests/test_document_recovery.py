import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.documents import PdfDownloader, is_probably_pdf, write_catalog_manifest


def test_pdf_magic_rejects_html_error_page():
    assert is_probably_pdf(b"%PDF-1.7\nexample") is True
    assert is_probably_pdf(b"<html>access denied</html>") is False


def test_download_filename_is_stable_and_not_source_name():
    url = "https://example.org/reports/audit.pdf?token=ignored"
    filename = PdfDownloader.filename_for_url(url)
    assert filename.startswith("rtrs_")
    assert filename.endswith(".pdf")
    assert filename == PdfDownloader.filename_for_url(url)


def test_catalog_manifest_preserves_url_and_flags_duplicates(tmp_path: Path):
    source = tmp_path / "source.csv"
    source.write_text(
        "Names,Country,Year,Links\nA,Brazil,2024,https://example.org/a.pdf\nB,Brazil,2024,https://example.org/a.pdf\n",
        encoding="utf-8",
    )
    output = tmp_path / "catalog.csv"

    assert write_catalog_manifest(source, output) == 2
    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["source_url"] == "https://example.org/a.pdf"
    assert rows[0]["url_duplicate"] == "false"
    assert rows[1]["url_duplicate"] == "true"

