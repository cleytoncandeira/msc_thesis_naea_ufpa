"""Estatísticas simples sobre relatórios organizados."""

from __future__ import annotations

from pathlib import Path
from typing import Dict


def count_reports_by_company(base_dir: Path) -> Dict[str, int]:
    """Conta quantos relatórios existem por empresa."""

    counts: Dict[str, int] = {}
    for company_dir in base_dir.iterdir():
        if not company_dir.is_dir():
            continue
        report_count = sum(1 for item in company_dir.iterdir() if item.is_dir())
        counts[company_dir.name] = report_count
    return counts


def find_companies_below_threshold(counts: Dict[str, int], minimum: int) -> Dict[str, int]:
    """Filtra empresas com menos relatórios que o mínimo desejado."""

    return {company: total for company, total in counts.items() if total < minimum}
