"""Extração progressiva e rastreável de texto de PDFs RTRS."""

from __future__ import annotations

import json
import re
import subprocess
import csv
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from .documents import sha256_file, utc_now


CRITERIA = tuple(f"{principle}.{criterion}" for principle, total in ((1, 3), (2, 5), (3, 4), (4, 5), (5, 11)) for criterion in range(1, total + 1))


@dataclass(frozen=True)
class PageText:
    document_id: str
    document_path: str
    document_sha256: str
    page_number: int
    text: str
    extraction_method: str
    extraction_status: str
    extracted_at_utc: str


@dataclass(frozen=True)
class CriterionEvidence:
    document_id: str
    document_path: str
    page_number: int
    criterion_id: str
    excerpt: str
    method: str
    validation_status: str


def extract_native_pages(pdf_path: Path, *, timeout_seconds: int = 180) -> list[PageText]:
    """Extrai texto incorporado, separando páginas pelo form-feed do Poppler.

    Páginas vazias são registradas como ``needs_ocr``; OCR é uma etapa posterior e
    nunca é disparado implicitamente por esta função.
    """

    document_sha = sha256_file(pdf_path)
    document_id = f"sha256:{document_sha}"
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        raw_pages = result.stdout.split("\f")
    except (FileNotFoundError, subprocess.SubprocessError):
        return [
            PageText(document_id, str(pdf_path), document_sha, 0, "", "native_text", "extraction_error", utc_now())
        ]

    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()
    return [
        PageText(
            document_id=document_id,
            document_path=str(pdf_path),
            document_sha256=document_sha,
            page_number=index,
            text=text.strip(),
            extraction_method="native_text",
            extraction_status="extracted" if text.strip() else "needs_ocr",
            extracted_at_utc=utc_now(),
        )
        for index, text in enumerate(raw_pages, start=1)
    ]


def _extract_one(pdf_path: Path) -> tuple[Path, list[PageText]]:
    return pdf_path, extract_native_pages(pdf_path)


def extract_corpus_native(pdf_dir: Path, *, workers: int = 2) -> Iterator[PageText]:
    """Extrai o corpus em poucos processos e em ordem estável de arquivo/página."""

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = dict(executor.map(_extract_one, pdfs))
    for pdf_path in pdfs:
        yield from results[pdf_path]


def criterion_evidence(page: PageText, *, context_characters: int = 900) -> list[CriterionEvidence]:
    """Localiza menções explícitas de critérios sem concluir conformidade."""

    if page.extraction_status != "extracted":
        return []
    evidence: list[CriterionEvidence] = []
    for criterion in CRITERIA:
        # Evita aceitar 1.1 dentro de 1.10 e exige um delimitador textual.
        pattern = re.compile(rf"(?<![\d.]){re.escape(criterion)}(?![\d.])")
        for match in pattern.finditer(page.text):
            left = max(0, match.start() - context_characters // 3)
            right = min(len(page.text), match.end() + (2 * context_characters // 3))
            excerpt = page.text[left:right].strip()
            evidence.append(
                CriterionEvidence(
                    document_id=page.document_id,
                    document_path=page.document_path,
                    page_number=page.page_number,
                    criterion_id=criterion,
                    excerpt=excerpt,
                    method="regex_explicit_criterion_reference",
                    validation_status="candidate_not_interpreted",
                )
            )
    return evidence


def write_jsonl(path: Path, rows: Iterable[object]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_processing_registry(pages_path: Path, registry_path: Path, ocr_queue_path: Path) -> tuple[int, int]:
    """Classifica cada documento a partir da extração nativa e cria fila seletiva OCR.

    ``mixed_or_blank_pages`` é deliberadamente conservador: uma página sem texto pode
    ser capa vazia. A decisão de OCR deve ser confirmada na etapa seguinte, página a
    página, antes de usar o texto em extração estruturada.
    """

    grouped: dict[str, list[dict]] = {}
    for page in read_jsonl(pages_path):
        grouped.setdefault(page["document_id"], []).append(page)

    registry_rows = []
    queue_rows = []
    for document_id, pages in sorted(grouped.items()):
        extracted = [page for page in pages if page["extraction_status"] == "extracted"]
        pending = [page for page in pages if page["extraction_status"] == "needs_ocr"]
        errors = [page for page in pages if page["extraction_status"] == "extraction_error"]
        classification = (
            "extraction_error" if errors else
            "digital_text" if len(extracted) == len(pages) else
            "mixed_or_blank_pages" if extracted else
            "image_only_or_unreadable"
        )
        registry_rows.append(
            {
                "document_id": document_id,
                "document_path": pages[0]["document_path"],
                "document_sha256": pages[0]["document_sha256"],
                "total_pages": len(pages),
                "native_text_pages": len(extracted),
                "ocr_candidate_pages": len(pending),
                "extraction_error_pages": len(errors),
                "document_classification": classification,
            }
        )
        for page in pending:
            queue_rows.append(
                {
                    "document_id": document_id,
                    "document_path": page["document_path"],
                    "page_number": page["page_number"],
                    "reason": "no_native_text_confirm_visual_before_ocr",
                    "status": "pending_review",
                }
            )

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("w", encoding="utf-8", newline="") as handle:
        fields = list(registry_rows[0]) if registry_rows else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(registry_rows)
    with ocr_queue_path.open("w", encoding="utf-8", newline="") as handle:
        fields = ["document_id", "document_path", "page_number", "reason", "status"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(queue_rows)
    return len(registry_rows), len(queue_rows)


def ocr_approved_pages(decisions_path: Path, output_path: Path, *, dpi: int = 200) -> int:
    """Executa Tesseract somente para páginas explicitamente aprovadas em revisão.

    A decisão não é inferida pelo código: cada linha precisa ter
    ``decision=ocr_approved``. A ausência de pacote linguístico apropriado deve ser
    tratada como limitação de qualidade, não como falha silenciosa.
    """

    results: list[PageText] = []
    with decisions_path.open(encoding="utf-8", newline="") as handle:
        decisions = [row for row in csv.DictReader(handle) if row.get("decision") == "ocr_approved"]
    for row in decisions:
        pdf_path = Path(row["document_path"])
        page_number = int(row["page_number"])
        document_sha = sha256_file(pdf_path)
        document_id = f"sha256:{document_sha}"
        try:
            with tempfile.TemporaryDirectory(prefix="rtrs_ocr_") as temp_dir:
                prefix = Path(temp_dir) / "page"
                subprocess.run(
                    ["pdftoppm", "-f", str(page_number), "-l", str(page_number), "-r", str(dpi), "-png", str(pdf_path), str(prefix)],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
                image_path = next(Path(temp_dir).glob("page-*.png"))
                ocr = subprocess.run(
                    ["tesseract", str(image_path), "stdout", "-l", "eng"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            text = ocr.stdout.strip()
            status = "extracted_low_confidence_language" if text else "ocr_no_text"
        except (FileNotFoundError, StopIteration, subprocess.SubprocessError):
            text = ""
            status = "ocr_error"
        results.append(
            PageText(document_id, str(pdf_path), document_sha, page_number, text, "ocr_tesseract_eng", status, utc_now())
        )
    return write_jsonl(output_path, results)
