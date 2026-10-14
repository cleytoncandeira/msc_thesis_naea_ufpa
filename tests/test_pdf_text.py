import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.pdf_text import PageText, criterion_evidence, write_jsonl, write_processing_registry


def test_criterion_evidence_finds_explicit_label_without_prefix_collision():
    page = PageText("doc", "file.pdf", "hash", 3, "Critério 1.1 atendido. 1.10 não é critério RTRS.", "native_text", "extracted", "now")
    evidence = criterion_evidence(page)
    assert [item.criterion_id for item in evidence] == ["1.1"]
    assert evidence[0].validation_status == "candidate_not_interpreted"


def test_empty_page_does_not_create_evidence():
    page = PageText("doc", "file.pdf", "hash", 3, "", "native_text", "needs_ocr", "now")
    assert criterion_evidence(page) == []


def test_processing_registry_queues_only_pages_without_native_text(tmp_path: Path):
    pages = [
        PageText("a", "a.pdf", "h1", 1, "text", "native_text", "extracted", "now"),
        PageText("a", "a.pdf", "h1", 2, "", "native_text", "needs_ocr", "now"),
        PageText("b", "b.pdf", "h2", 1, "text", "native_text", "extracted", "now"),
    ]
    input_path = tmp_path / "pages.jsonl"
    write_jsonl(input_path, pages)
    documents, candidates = write_processing_registry(input_path, tmp_path / "registry.csv", tmp_path / "queue.csv")
    assert (documents, candidates) == (2, 1)
    assert "mixed_or_blank_pages" in (tmp_path / "registry.csv").read_text(encoding="utf-8")
