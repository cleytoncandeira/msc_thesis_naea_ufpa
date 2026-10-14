"""CLI da Fase 2: inventário local, catálogo RTRS e download deliberado."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.documents import PdfDownloader, write_catalog_manifest, write_document_manifest, write_download_log


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Recuperação documental RTRS (Fase 2).")
    command.add_argument("--pdf-dir", type=Path, default=PROJECT_ROOT / "data/external_data/audit_reports")
    command.add_argument("--catalog", type=Path, default=PROJECT_ROOT / "data/external_data/certified_producers_rtrs.csv")
    command.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs/reports")
    command.add_argument("--inventory", action="store_true", help="Inventaria PDFs locais sem alterá-los.")
    command.add_argument("--catalog-manifest", action="store_true", help="Normaliza o catálogo existente sem acessar a rede.")
    command.add_argument("--download", action="store_true", help="Baixa as URLs do catálogo: operação de rede explícita.")
    command.add_argument("--workers", type=int, default=2)
    command.add_argument("--min-interval", type=float, default=0.5)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ran = False
    if args.inventory:
        records = write_document_manifest(args.pdf_dir, args.output_dir / "document_manifest.csv")
        print(f"Inventário salvo: {len(records)} documentos")
        ran = True
    if args.catalog_manifest:
        count = write_catalog_manifest(args.catalog, args.output_dir / "catalog_manifest.csv")
        print(f"Catálogo normalizado: {count} registros")
        ran = True
    if args.download:
        with args.catalog.open(encoding="utf-8", newline="") as handle:
            urls = [row.get("Links", "") for row in csv.DictReader(handle)]
        downloader = PdfDownloader(args.pdf_dir, min_interval_seconds=args.min_interval)
        results = list(downloader.download_many(urls, max_workers=args.workers))
        write_download_log(results, args.output_dir / "download_log.csv")
        print(f"Download concluído: {sum(r.status in {'downloaded', 'already_valid'} for r in results)}/{len(results)} válidos")
        ran = True
    if not ran:
        parser().print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
