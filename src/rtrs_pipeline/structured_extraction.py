"""Extração determinística, conservadora e rastreável de metadados RTRS."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional


@dataclass(frozen=True)
class MetadataEvidence:
    document_id: str
    document_path: str
    page_number: int
    field_name: str
    value_raw: str
    value_normalized: str
    value_numeric: str
    evidence_text: str
    source_extraction_method: str
    extraction_method: str
    validation_status: str


FIELD_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "certificate_code": (
        # Exige ao menos um dígito: expressões como "RTRS Standard" ou
        # "RTRS member" não são códigos de certificado.
        re.compile(r"\b(RTRS[-A-Z0-9.]*\d[-A-Z0-9.]*)\b", re.I),
        re.compile(r"\b(FCID\s+RTRS\s+\d+(?:\s+\d+)?)\b", re.I),
        re.compile(r"\b(CUC[-A-Z0-9.]*\d[-A-Z0-9.]*)\b", re.I),
    ),
    "audit_date": (
        re.compile(r"(?:audit\s*date|data\s*(?:da|de)\s*auditoria)\s*[:#-]\s*([^\n]{6,80})", re.I),
    ),
    "issue_date": (
        re.compile(r"(?:certificate\s*start\s*date|data\s*(?:de\s*)?(?:emiss[aã]o|in[ií]cio))\s*[:#-]\s*([^\n]{6,80})", re.I),
    ),
    "expiration_date": (
        re.compile(r"(?:certificate\s*end\s*date|validade\s*(?:do\s*)?certificado|expiration\s*date)\s*[:#-]\s*([^\n]{6,80})", re.I),
    ),
    "enterprise_type": (
        re.compile(r"(?:certificate\s*type|tipo\s*(?:de\s*)?(?:certificado|avalia[cç][aã]o|empreendimento))\s*[:#-]\s*([^\n]{3,120})", re.I),
    ),
    "member_count": (
        re.compile(r"(?:n[uú]mero\s*total\s*de\s*membros|number\s*of\s*members|n[°ºo]\s*(?:de\s*)?membros)\s*[:#-]?\s*(\d{1,6})", re.I),
    ),
    "certified_area_ha": (
        re.compile(r"(?:[aá]rea\s*certificada|certified\s*area)\s*(?:\(?(?:ha|hectares?)\)?)?\s*[:#-]\s*([^\n]{1,100})", re.I),
    ),
    "certified_soy_area_ha": (
        re.compile(r"(?:[aá]rea\s*de\s*soja\s*a\s*ser\s*certificada|[aá]rea\s*certificada\s*de\s*soja)\s*(?:\(?(?:ha|hectares?)\)?)?\s*[:#-]\s*(?:soja\s*:\s*)?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)", re.I),
    ),
    "certified_corn_area_ha": (
        re.compile(r"(?:[aá]rea\s*de\s*soja\s*a\s*ser\s*certificada|[aá]rea\s*certificada\s*de\s*soja)[\s\S]{0,120}?(?:milho|corn)\s*:\s*(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)", re.I),
    ),
    "cultivated_area_ha": (
        re.compile(r"(?:[aá]rea\s*(?:cultivada|plantada|produzida|de\s*produ[cç][aã]o)|planted\s*area|production\s*area)\s*(?:\(?(?:ha|hectares?)\)?)?\s*[:#-]\s*([^\n]{1,100})", re.I),
    ),
    "cultivated_soy_area_ha": (
        re.compile(r"(?:[aá]rea\s*(?:cultivada|plantada|produzida)\s*(?:de\s*)?soja|soy\s*(?:cultivated|planted|production)\s*area)\s*(?:\(?(?:ha|hectares?)\)?)?\s*[:#-]\s*(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)", re.I),
    ),
    "cultivated_corn_area_ha": (
        re.compile(r"(?:[aá]rea\s*(?:cultivada|plantada|produzida)\s*(?:de\s*)?(?:milho|corn)|(?:milho|corn)\s*(?:cultivated|planted|production)\s*area)\s*(?:\(?(?:ha|hectares?)\)?)?\s*[:#-]\s*(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?)", re.I),
    ),
    "total_area_ha": (
        re.compile(r"(?:[aá]rea\s*total|total\s*area)\s*(?:\(?(?:ha|hectares?)\)?)?\s*[:#-]\s*([^\n]{1,100})", re.I),
    ),
    "certified_production_tonnes": (
        re.compile(r"(?:produ[cç][aã]o|production)\s*(?:\(?(?:ton(?:eladas)?|t|real)\)?)?\s*[:#-]\s*([^\n]{1,100})", re.I),
    ),
    "enterprise_name": (
        re.compile(r"(?:nome\s*(?:da\s*)?(?:fazenda|organiza[cç][aã]o|empreendimento)|establishment|producer)\s*[:#-]\s*([^\n]{3,150})", re.I),
    ),
    "auditor": (
        re.compile(r"(?:organismo\s*de\s*certifica[cç][aã]o|certification\s*body|empresa\s*auditora|auditor)\s*[:#-]\s*([^\n]{3,150})", re.I),
    ),
}


def clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-\t")


def normalize_number(value: str) -> Optional[str]:
    """Normaliza um número apenas quando há um único candidato inequívoco."""

    candidates = re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+\.\d+|\d+(?:,\d+)?", value)
    if len(candidates) != 1:
        return None
    numeric = candidates[0]
    if "." in numeric and "," in numeric:
        numeric = numeric.replace(".", "").replace(",", ".")
    elif "," in numeric:
        numeric = numeric.replace(",", ".")
    try:
        return f"{float(numeric):.10g}"
    except ValueError:
        return None


def extract_metadata_from_page(page: dict) -> list[MetadataEvidence]:
    """Extrai candidatos por regex; nunca declara um campo como validado."""

    if not page.get("text"):
        return []
    output: list[MetadataEvidence] = []
    text = page["text"]
    for field_name, patterns in FIELD_PATTERNS.items():
        seen: set[str] = set()
        for pattern in patterns:
            for match in pattern.finditer(text):
                raw = clean_value(match.group(1))
                if not raw or raw in seen:
                    continue
                seen.add(raw)
                numeric = normalize_number(raw) if field_name in {"member_count", "certified_area_ha", "certified_soy_area_ha", "certified_corn_area_ha", "cultivated_area_ha", "cultivated_soy_area_ha", "cultivated_corn_area_ha", "total_area_ha", "certified_production_tonnes"} else None
                start = max(0, match.start() - 160)
                end = min(len(text), match.end() + 260)
                output.append(
                    MetadataEvidence(
                        document_id=page["document_id"],
                        document_path=page["document_path"],
                        page_number=int(page["page_number"]),
                        field_name=field_name,
                        value_raw=raw,
                        value_normalized=raw,
                        value_numeric=numeric or "",
                        evidence_text=text[start:end].replace("\n", " ").strip(),
                        source_extraction_method=page["extraction_method"],
                        extraction_method=f"regex:{pattern.pattern[:48]}",
                        validation_status="candidate_not_validated",
                    )
                )
    return output


def read_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[MetadataEvidence]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
            count += 1
    return count


def write_candidates_csv(jsonl_path: Path, output_csv: Path) -> int:
    rows = list(read_jsonl(jsonl_path))
    fields = list(MetadataEvidence.__dataclass_fields__)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
