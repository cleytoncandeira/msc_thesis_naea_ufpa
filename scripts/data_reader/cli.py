"""Command-line interface for the audit report preprocessing pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .paths import (
    ORGANIZED_REPORTS_DIR,
    RAW_REPORTS_DIR,
    REPORT_IMAGES_DIR,
    ensure_default_directories,
    ensure_directory,
)
from .pdf_processing import convert_pdfs_to_images
from .report_organizer import organize_reports
from .report_stats import count_reports_by_company, find_companies_below_threshold
from .annotation_tool import annotate_companies
from .ocr_dataset import build_dataset_from_reports


DEFAULT_VARIABLES: List[str] = [
    "endereço",
    "cod_certificado",
    "validade_certificado",
    "nome_organização",
    "tipo_avaliacao",
    "area_total",
    "producao",
    "data_prox_auditoria",
]

DEFAULT_LIMITS: Dict[str, int] = {
    "Control Union": 5,
    "SGS Argentina": 2,
    "Food Chain ID": 5,
    "Genesis Certificações": 3,
    "Bureau Veritas": 3,
    "Cert ID": 2,
}


def _path(value: str) -> Path:
    """Converte argumento textual em Path absoluto."""

    return Path(value).expanduser().resolve()


def _load_json(path: Optional[Path]) -> Optional[Any]:
    """Carrega JSON caso um caminho tenha sido informado."""

    if path is None:
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos do CLI."""

    parser = argparse.ArgumentParser(
        description="Pipeline CLI para pré-processamento de relatórios de auditoria",
    )

    parser.add_argument(
        "--raw-dir",
        type=_path,
        default=RAW_REPORTS_DIR,
        help="Diretório com PDFs brutos.",
    )
    parser.add_argument(
        "--images-dir",
        type=_path,
        default=REPORT_IMAGES_DIR,
        help="Diretório onde as imagens geradas serão armazenadas.",
    )
    parser.add_argument(
        "--organized-dir",
        type=_path,
        default=ORGANIZED_REPORTS_DIR,
        help="Diretório organizado por empresa.",
    )

    parser.add_argument("--convert", action="store_true", help="Converter PDFs em imagens.")
    parser.add_argument("--dpi", type=int, default=120, help="DPI usado na conversão de PDFs.")

    parser.add_argument("--organize", action="store_true", help="Organizar relatórios por empresa.")

    parser.add_argument("--stats", action="store_true", help="Exibir contagem de relatórios por empresa.")
    parser.add_argument(
        "--min-reports",
        type=int,
        default=5,
        help="Número mínimo recomendado de relatórios por empresa.",
    )

    parser.add_argument("--annotate", action="store_true", help="Iniciar anotação manual com OpenCV.")
    parser.add_argument(
        "--variables-file",
        type=_path,
        help="Arquivo JSON contendo a lista de variáveis a serem anotadas.",
    )
    parser.add_argument(
        "--limits-file",
        type=_path,
        help="Arquivo JSON com o limite de relatórios por empresa (dict de empresa->int).",
    )

    parser.add_argument(
        "--dataset",
        action="store_true",
        help="Gerar dataset anotado (JSONL) a partir dos relatórios organizados.",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="IOU mínimo para associar tokens durante a criação do dataset.",
    )
    parser.add_argument(
        "--use-center",
        action="store_true",
        help="Usar interseção pelo centro do token em vez de IOU.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Exibe as ações que seriam executadas sem rodar nenhuma etapa.",
    )

    return parser


def _resolve_variables(path: Optional[Path]) -> List[str]:
    """Carrega a lista de variáveis ou usa as padrão."""

    loaded = _load_json(path)
    if loaded is None:
        return DEFAULT_VARIABLES
    if not isinstance(loaded, list):
        raise ValueError("O arquivo de variáveis deve conter uma lista JSON.")
    return [str(item) for item in loaded]


def _resolve_limits(path: Optional[Path]) -> Dict[str, int]:
    """Carrega o dicionário de limites por empresa ou usa o padrão."""

    loaded = _load_json(path)
    if loaded is None:
        return DEFAULT_LIMITS
    if not isinstance(loaded, dict):
        raise ValueError("O arquivo de limites deve conter um dicionário JSON.")
    return {str(company): int(limit) for company, limit in loaded.items()}


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Executa o pipeline CLI para leitura e anotação."""

    parser = build_parser()
    args = parser.parse_args(argv)

    raw_dir: Path = args.raw_dir
    images_dir: Path = args.images_dir
    organized_dir: Path = args.organized_dir

    actions: List[str] = []
    if args.convert:
        actions.append("converter PDFs")
    if args.organize:
        actions.append("organizar relatórios")
    if args.stats:
        actions.append("gerar estatísticas")
    if args.annotate:
        actions.append("anotar relatórios")
    if args.dataset:
        actions.append("construir dataset anotado")

    if args.dry_run:
        print("Dry run: nenhuma etapa será executada.")
        print("Diretórios:")
        print(f"- RAW: {raw_dir}")
        print(f"- IMAGES: {images_dir}")
        print(f"- ORGANIZED: {organized_dir}")
        if actions:
            print("Etapas selecionadas: " + ", ".join(actions))
        else:
            print("Nenhuma etapa selecionada.")
        return 0

    ensure_default_directories()
    ensure_directory(images_dir)
    ensure_directory(organized_dir)

    if args.convert:
        print(f"[CONVERT] PDFs em {raw_dir} -> imagens em {images_dir} (dpi={args.dpi})")
        convert_pdfs_to_images(raw_dir, images_dir, dpi=args.dpi)

    if args.organize:
        print(f"[ORGANIZE] Organizando relatórios de {images_dir} -> {organized_dir}")
        organize_reports(images_dir, organized_dir)

    if args.stats:
        print("[STATS] Contando relatórios por empresa")
        counts = count_reports_by_company(organized_dir)
        for company, total in counts.items():
            print(f"- {company}: {total}")
        deficit = find_companies_below_threshold(counts, minimum=args.min_reports)
        if deficit:
            print("Empresas abaixo do mínimo:")
            for company, total in deficit.items():
                print(f"  * {company}: {total} < {args.min_reports}")

    if args.annotate:
        variables = _resolve_variables(args.variables_file)
        limits = _resolve_limits(args.limits_file)
        print("[ANNOTATE] Iniciando anotação manual")
        print(f"Variáveis ({len(variables)}): {', '.join(variables)}")
        annotate_companies(organized_dir, variables=variables, limits=limits)

    if args.dataset:
        print("[DATASET] Construindo dataset JSONL")
        build_dataset_from_reports(
            organized_dir,
            iou_threshold=args.iou_threshold,
            use_center=args.use_center,
        )

    if not actions:
        print("Nenhuma etapa selecionada. Use --help para ver as opções.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
