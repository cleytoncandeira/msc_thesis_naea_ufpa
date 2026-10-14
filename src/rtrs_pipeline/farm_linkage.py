"""Liga documentos com vínculo histórico seguro às fazendas georreferenciadas."""

from __future__ import annotations

from rtrs_pipeline.legacy_linkage import canonical_text


def document_farm_rows(register: list[dict], farms: list[dict]) -> list[dict]:
    rows = []
    seen: set[tuple[str, str, str, str]] = set()
    for document in register:
        if document.get("legacy_match_status") not in {"linked_exact_name_certificate_year", "linked_exact_entity_and_year_code_unavailable"}:
            continue
        entities = {canonical_text(document.get("legacy_Organization", "")), canonical_text(document.get("legacy_Name", ""))}
        entities.discard("")
        for farm in farms:
            farm_entities = {canonical_text(farm.get("Organization", "")), canonical_text(farm.get("Name", ""))}
            if not entities.intersection(farm_entities):
                continue
            key = (document["document_id"], farm.get("Farm", ""), farm.get("Latitude", ""), farm.get("Longitude", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "document_id": document["document_id"], "document_path": document["document_path"],
                "legacy_record_id": document["legacy_record_id"], "legacy_organization": document.get("legacy_Organization", ""),
                "legacy_name": document.get("legacy_Name", ""), "farm": farm.get("Farm", ""),
                "state": farm.get("State", ""), "city": farm.get("City", ""),
                "latitude": farm.get("Latitude", ""), "longitude": farm.get("Longitude", ""),
                "link_method": "exact_legacy_entity_to_farm_branch",
            })
    return sorted(rows, key=lambda row: (row["document_id"], row["farm"], row["latitude"]))
