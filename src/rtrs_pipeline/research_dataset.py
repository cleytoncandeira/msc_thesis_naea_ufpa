"""Monta uma tabela de pesquisa a partir de campos já promovidos e rastreáveis."""

from __future__ import annotations

from rtrs_pipeline.structured_extraction import normalize_number


def research_rows(metadata_rows: list[dict], crop_rows: list[dict]) -> list[dict]:
    """Une fontes promovidas e impede duas versões do mesmo documento/campo."""

    output = []
    seen: set[tuple[str, str]] = set()
    for row in metadata_rows + crop_rows:
        key = (row["document_id"], row["field_name"])
        if key in seen:
            raise ValueError(f"Campo promovido duplicado: {key}")
        seen.add(key)
        raw = row.get("selected_value_raw", "")
        numeric = row.get("selected_value_numeric", "")
        if not numeric and row["field_name"].endswith("_area_ha"):
            numeric = normalize_number(raw) or ""
        output.append({
            "document_id": row["document_id"],
            "document_path": row["document_path"],
            "field_name": row["field_name"],
            "value_raw": raw,
            "value_normalized": row.get("selected_value_normalized", "") or raw,
            "value_numeric": numeric,
            "candidate_pages": row.get("candidate_pages", ""),
            "promotion_status": row.get("promotion_status", ""),
            "human_decision": row.get("human_decision", ""),
            "review_excerpt": row.get("review_excerpt", ""),
        })
    return sorted(output, key=lambda row: (row["document_id"], row["field_name"]))
