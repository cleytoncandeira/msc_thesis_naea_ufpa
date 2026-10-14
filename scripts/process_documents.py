"""CLI inicial para Fase 3: texto por página e candidatos de critério."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.pdf_text import PageText, criterion_evidence, extract_corpus_native, ocr_approved_pages, read_jsonl, write_jsonl, write_processing_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fase 3: extração textual rastreável de PDFs RTRS.")
    parser.add_argument("--pdf-dir", type=Path, default=PROJECT_ROOT / "data/external_data/audit_reports")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/intermediate")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--extract-native", action="store_true")
    parser.add_argument("--criterion-evidence", action="store_true")
    parser.add_argument("--processing-registry", action="store_true", help="Classifica PDFs e cria fila seletiva de OCR, sem executar OCR.")
    parser.add_argument("--ocr-decisions", type=Path, help="CSV de decisões de revisão para OCR seletivo.")
    parser.add_argument("--ocr-approved", action="store_true", help="Executa OCR somente nas linhas ocr_approved.")
    parser.add_argument("--prepare-reviewed-ocr", action="store_true", help="Registra decisões desta revisão visual estratificada da fila atual.")
    args = parser.parse_args(argv)
    pages_path = args.output_dir / "pages_native.jsonl"
    if args.extract_native:
        count = write_jsonl(pages_path, extract_corpus_native(args.pdf_dir, workers=args.workers))
        print(f"Páginas registradas: {count}")
    if args.criterion_evidence:
        if not pages_path.exists():
            parser.error("Execute --extract-native antes de --criterion-evidence.")
        pages = (PageText(**row) for row in read_jsonl(pages_path))
        evidence = (item for page in pages for item in criterion_evidence(page))
        count = write_jsonl(args.output_dir / "criterion_evidence_candidates.jsonl", evidence)
        print(f"Evidências candidatas registradas: {count}")
    if args.processing_registry:
        if not pages_path.exists():
            parser.error("Execute --extract-native antes de --processing-registry.")
        documents, candidates = write_processing_registry(
            pages_path,
            args.output_dir / "document_processing_registry.csv",
            args.output_dir / "ocr_review_queue.csv",
        )
        print(f"Registro de processamento: {documents} documentos; fila OCR: {candidates} páginas")
    if args.ocr_approved:
        if not args.ocr_decisions:
            parser.error("--ocr-approved exige --ocr-decisions.")
        count = ocr_approved_pages(args.ocr_decisions, args.output_dir / "ocr_text.jsonl")
        print(f"Páginas OCR registradas: {count}")
    if args.prepare_reviewed_ocr:
        queue_path = args.output_dir / "ocr_review_queue.csv"
        if not queue_path.exists():
            parser.error("Execute --processing-registry antes de --prepare-reviewed-ocr.")
        with queue_path.open(encoding="utf-8", newline="") as handle:
            queue = list(csv.DictReader(handle))
        decisions = []
        for row in queue:
            blank = row["document_path"].endswith("audit_report_rtrs141.pdf") or row["document_path"].endswith("audit_report_rtrs211.pdf")
            decisions.append(
                row | {
                    "decision": "skip_blank" if blank else "ocr_approved",
                    "decision_reason": "visual_review_confirmed_blank_page" if blank else "representative_visual_review_confirmed_image_cover_with_cadastral_text",
                    "review_method": "stratified_visual_review_2026-10-13",
                }
            )
        decisions_path = args.output_dir / "ocr_review_decisions.csv"
        with decisions_path.open("w", encoding="utf-8", newline="") as handle:
            fields = list(decisions[0])
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(decisions)
        print(f"Decisões OCR registradas: {len(decisions)}")
    if not args.extract_native and not args.criterion_evidence and not args.processing_registry and not args.ocr_approved and not args.prepare_reviewed_ocr:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

