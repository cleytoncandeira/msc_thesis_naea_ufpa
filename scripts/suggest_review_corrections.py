"""Cria cópia revisável para casos accept sem valor selecionado."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from rtrs_pipeline.structured_extraction import extract_metadata_from_page


DATE = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
NUMBER = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?"


def atomic_suggestion(field_name: str, text: str) -> str:
    """Extrai somente um valor curto onde o campo tem formato conhecido."""

    labels = {
        "audit_date": r"(?:data|datas)\s*(?:da|de)\s*auditoria|audit\s*date",
        "issue_date": r"data\s*(?:de\s*)?(?:emiss[aã]o|in[ií]cio)|certificate\s*start\s*date",
        "expiration_date": r"validade\s*(?:do\s*)?certificado|certificate\s*end\s*date|expiration\s*date",
    }
    if field_name in labels:
        match = re.search(rf"(?:{labels[field_name]}).{{0,90}}?({DATE})", text, re.I | re.S)
        return match.group(1) if match else ""
    numeric_labels = {
        "certified_area_ha": r"(?:[aá]rea\s*(?:total|cultivada|certificada)|planted\s*area|certified\s*area)",
        "certified_production_tonnes": r"(?:produ[cç][aã]o|production)",
        "member_count": r"(?:n[uú]mero\s*total\s*de\s*membros|number\s*of\s*members|n[°ºo]\s*(?:de\s*)?membros)",
    }
    if field_name in numeric_labels:
        match = re.search(rf"(?:{numeric_labels[field_name]}).{{0,70}}?({NUMBER})", text, re.I | re.S)
        return match.group(1) if match else ""
    if field_name == "enterprise_type":
        match = re.search(r"(?:tipo\s*(?:de\s*)?(?:avalia[cç][aã]o|empreendimento)|certificate\s*type)\s*[:#-]?\s*(.{1,80}?)(?=\s+(?:certifica[cç][aã]o\s*parcial|datas?\s+de\s+auditoria|data\s+da\s+auditoria)|$)", text, re.I | re.S)
        return " ".join(match.group(1).split()) if match else ""
    if field_name == "enterprise_name":
        match = re.search(r"(?:nome\s*(?:da\s*)?(?:fazenda|organiza[cç][aã]o|empreendimento)|establishment|producer)\s*[:#-]?\s*(.{2,120}?)(?=\s+(?:pa[ií]s|pessoa\s+de\s+contato|contato|e-?mail|c[oó]digo\s+do\s+certificado)|$)", text, re.I | re.S)
        return " ".join(match.group(1).split()) if match else ""
    return ""


def suggestion_for_row(row: dict[str, str]) -> tuple[str, str]:
    atomic = atomic_suggestion(row["field_name"], row["review_excerpt"])
    if atomic:
        return atomic, "prefilled_atomic_value_from_excerpt"
    if row["field_name"] in {
        "audit_date", "issue_date", "expiration_date", "certified_area_ha",
        "certified_production_tonnes", "member_count", "enterprise_type", "enterprise_name",
    }:
        return "", "no_atomic_value_matched_by_rule"
    page = {
        "document_id": row["document_id"],
        "document_path": row["document_path"],
        "page_number": row.get("candidate_pages", "0").split("|")[0] or "0",
        "text": row["review_excerpt"],
        "extraction_method": "review_excerpt",
    }
    candidates = [item for item in extract_metadata_from_page(page) if item.field_name == row["field_name"]]
    values = list(dict.fromkeys(item.value_normalized for item in candidates))
    if len(values) == 1 and len(values[0]) <= 80:
        return values[0], "prefilled_from_review_excerpt"
    if len(values) > 1:
        return "", "multiple_values_in_excerpt"
    return "", "no_value_matched_by_rule"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera cópia com sugestões para accepts sem valor selecionado.")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "outputs/validation/metadata_human_validation.csv")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "outputs/validation/metadata_human_validation_suggested.csv")
    args = parser.parse_args(argv)

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    changed = 0
    statuses: dict[str, int] = {}
    for row in rows:
        if row["human_decision"].strip().casefold() == "accept" and not row["selected_value_raw"].strip():
            suggested, status = suggestion_for_row(row)
            row["human_decision"] = "correct"
            row["corrected_value"] = suggested
            row["review_notes"] = (row.get("review_notes") or "") + f" [proposal:{status}]"
            changed += 1
            statuses[status] = statuses.get(status, 0) + 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Linhas convertidas: {changed}; sugestões: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
