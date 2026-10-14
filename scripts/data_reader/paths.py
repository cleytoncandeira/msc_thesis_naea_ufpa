"""Caminhos padrão do pipeline de leitura de PDFs."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
EXTERNAL_DATA_DIR = DATA_DIR / "external_data"
RAW_REPORTS_DIR = EXTERNAL_DATA_DIR / "audit_reports"
PROCESSED_DATA_DIR = DATA_DIR / "processed_data"
REPORT_IMAGES_DIR = PROCESSED_DATA_DIR / "audit_reports_database"
ORGANIZED_REPORTS_DIR = PROCESSED_DATA_DIR / "organized_audit_reports"


def ensure_directory(path: Path) -> Path:
    """Garante que um diretório exista.

    Args:
        path: Caminho do diretório.

    Returns:
        O próprio caminho para uso encadeado.
    """

    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_default_directories() -> None:
    """Cria as pastas padrão do pipeline."""

    ensure_directory(REPORT_IMAGES_DIR)
    ensure_directory(ORGANIZED_REPORTS_DIR)
