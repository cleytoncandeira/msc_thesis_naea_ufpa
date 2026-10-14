"""Transforma metadados longos e promovidos em uma tabela por documento."""

from __future__ import annotations

from collections import Counter


def pivot_research_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Gera uma linha por documento e mede a cobertura de cada campo."""

    by_document: dict[str, dict] = {}
    counts: Counter[str] = Counter()
    for row in rows:
        document_id = row["document_id"]
        target = by_document.setdefault(document_id, {"document_id": document_id, "document_path": row["document_path"]})
        field = row["field_name"]
        if field in target:
            raise ValueError(f"Mais de um valor promovido para {document_id}/{field}")
        target[field] = row["value_normalized"]
        if row.get("value_numeric"):
            target[f"{field}__numeric"] = row["value_numeric"]
        target[f"{field}__provenance"] = row["promotion_status"]
        counts[field] += 1
    wide = sorted(by_document.values(), key=lambda row: row["document_id"])
    coverage = [
        {"field_name": field, "documents_with_value": count, "document_coverage_rate": round(count / len(wide), 4)}
        for field, count in sorted(counts.items())
    ]
    return wide, coverage
