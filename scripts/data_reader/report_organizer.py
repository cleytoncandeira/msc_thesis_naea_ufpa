"""Identificação e organização de relatórios por empresa."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, Optional, Set

from PIL import Image
import pytesseract

IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}

COMPANY_PATTERNS: Dict[str, str] = {
    "Food Chain ID": r"\bfood\s*chain\s*i[dn]\b",
    "Control Union": r"\bcontrol\s*union\b",
    "Genesis Certificações": r"\bgenesis\b",
    "Bureau Veritas": r"\bbureau\s*veritas\b",
    "SGS Argentina": r"\bsgs\s*argentina\b",
    "Cert ID": r"\bcert\s*i[dn]\b",
    "Imaflora": r"\bimaflora\b",
    "Schutter Argentina": r"\bschutter\s*argentina\b",
}


def identify_company(text: str, patterns: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Detecta a empresa responsável com base em padrões de texto."""

    compiled = patterns or COMPANY_PATTERNS
    for company, pattern in compiled.items():
        if re.search(pattern, text, re.IGNORECASE):
            return company
    return None


def read_report_text(report_dir: Path) -> str:
    """Executa OCR em todas as páginas do relatório para consolidar texto."""

    text_chunks = []
    for image_path in sorted(report_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        try:
            text_chunks.append(pytesseract.image_to_string(Image.open(image_path)))
        except Exception as exc:
            print(f"Erro ao processar {image_path}: {exc}")
    return "\n".join(text_chunks)


def organize_reports(source_root: Path, target_root: Path) -> None:
    """Move relatórios para pastas separadas por empresa."""

    target_root.mkdir(parents=True, exist_ok=True)
    report_dirs = [p for p in source_root.iterdir() if p.is_dir()]

    for report_dir in report_dirs:
        report_text = read_report_text(report_dir)
        company = identify_company(report_text)

        if not company:
            print(f"Empresa não identificada para: {report_dir.name}")
            continue

        company_dir = target_root / company
        company_dir.mkdir(parents=True, exist_ok=True)
        destination = company_dir / report_dir.name

        if destination.exists():
            print(f"Relatório já existe em destino: {destination}")
            continue

        shutil.move(str(report_dir), destination)


def iter_company_reports(base_dir: Path) -> Iterable[Path]:
    """Itera por todos os relatórios organizados em subpastas de empresas."""

    for company_dir in sorted(base_dir.iterdir()):
        if company_dir.is_dir():
            yield from (item for item in sorted(company_dir.iterdir()) if item.is_dir())
