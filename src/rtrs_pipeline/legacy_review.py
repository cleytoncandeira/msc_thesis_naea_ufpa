"""Prepara revisão humana de vínculos documento–base histórica."""

from __future__ import annotations

from collections import defaultdict


def legacy_linkage_review_queue(register: list[dict], candidates: list[dict]) -> list[dict]:
    """Uma linha por documento ainda não vinculado automaticamente."""

    grouped: dict[str, list[dict]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate["document_id"]].append(candidate)
    queue = []
    for row in register:
        if row.get("legacy_match_status") != "candidate_entity_match_requires_review":
            continue
        options = sorted(grouped[row["document_id"]], key=lambda item: (-int(item["match_score"]), int(item["legacy_record_id"])))
        proposed = options[0]
        option_text = " || ".join(
            f"id={item['legacy_record_id']}; organização={item['legacy_organization']}; nome={item['legacy_name']}; ano={item['legacy_year']}; certificado={item.get('legacy_regtag', '')}; link={item.get('legacy_links', '')}; ano_coincide={item['year_match']}"
            for item in options
        )
        queue.append({
            "document_id": row["document_id"],
            "document_path": row["document_path"],
            "enterprise_name_extracted": row.get("enterprise_name", ""),
            "certificate_code_extracted": row.get("certificate_code", ""),
            "document_dates": " | ".join(filter(None, (row.get("audit_date", ""), row.get("issue_date", ""), row.get("expiration_date", "")))),
            "proposed_legacy_record_id": proposed["legacy_record_id"],
            "proposed_organization": proposed["legacy_organization"],
            "proposed_name": proposed["legacy_name"],
            "proposed_year": proposed["legacy_year"],
            "proposed_certificate_code": proposed.get("legacy_regtag", ""),
            "proposed_legacy_link": proposed.get("legacy_links", ""),
            "candidate_options": option_text,
            "link_decision": "",
            "selected_legacy_record_id": "",
            "reviewer": "",
            "review_notes": "",
        })
    return queue
