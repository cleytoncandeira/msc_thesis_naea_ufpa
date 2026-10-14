"""Vinculação conservadora entre a base histórica RTRS e relatórios promovidos."""

from __future__ import annotations

import re
import unicodedata


def canonical_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().casefold()
    value = re.sub(r"\b(ltda|lt|s\s*a|sa|eireli|me)\b", " ", value)
    return " ".join(re.findall(r"[a-z0-9]+", value))


def canonical_certificate(value: str) -> str:
    """Remove pontuação para comparar códigos RTRS sem perder os dígitos."""

    return "".join(re.findall(r"[a-z0-9]+", (value or "").casefold()))


def years_in_row(row: dict) -> set[str]:
    years = set(re.findall(r"(?:19|20)\d{2}", " ".join(str(row.get(key, "")) for key in ("audit_date", "issue_date", "expiration_date"))))
    for short_year in re.findall(r"(?:^|\D)(\d{2})(?:\D|$)", " ".join(str(row.get(key, "")) for key in ("audit_date", "issue_date", "expiration_date"))):
        years.add(f"20{short_year}")
    return years


def link_legacy_rows(documents: list[dict], legacy: list[dict]) -> tuple[list[dict], list[dict]]:
    """Associa somente nome exato + ano coincidente, conservando candidatos restantes."""

    register, candidates = [], []
    for doc in documents:
        name = canonical_text(doc.get("enterprise_name", ""))
        document_certificate = canonical_certificate(doc.get("certificate_code", ""))
        document_years = years_in_row(doc)
        matches = []
        if name:
            for index, historic in enumerate(legacy):
                entity_match = name in {canonical_text(historic.get("Organization", "")), canonical_text(historic.get("Name", ""))}
                if entity_match:
                    year_match = historic.get("Year", "") in document_years
                    historic_certificate = canonical_certificate(historic.get("RegTag", ""))
                    certificate_available = bool(document_certificate and historic_certificate)
                    certificate_match = certificate_available and document_certificate == historic_certificate
                    # Um código disponível e divergente impede vínculo automático.
                    score = 100 + (40 if year_match else 0) + (80 if certificate_match else 0)
                    matches.append((score, index, historic, year_match, certificate_available, certificate_match))
        matches.sort(key=lambda item: (-item[0], item[1]))
        best = matches[0] if matches else None
        exact_identity = bool(best and best[3] and best[5] and (len(matches) == 1 or best[0] > matches[1][0]))
        unique_name_year_without_code = bool(best and best[3] and not best[4] and (len(matches) == 1 or best[0] > matches[1][0]))
        output = dict(doc)
        output["legacy_match_status"] = "linked_exact_name_certificate_year" if exact_identity else "linked_exact_entity_and_year_code_unavailable" if unique_name_year_without_code else "candidate_entity_match_requires_review" if matches else "no_legacy_entity_match"
        output["legacy_match_score"] = str(best[0]) if best else ""
        output["legacy_record_id"] = str(best[1]) if exact_identity or unique_name_year_without_code else ""
        if exact_identity or unique_name_year_without_code:
            for key, value in best[2].items():
                output[f"legacy_{key}"] = value
        register.append(output)
        for score, index, historic, year_match, certificate_available, certificate_match in matches:
            candidates.append({
                "document_id": doc["document_id"], "document_path": doc["document_path"], "enterprise_name": doc.get("enterprise_name", ""),
                "document_years": "|".join(sorted(document_years)), "legacy_record_id": index,
                "legacy_organization": historic.get("Organization", ""), "legacy_name": historic.get("Name", ""),
                "legacy_year": historic.get("Year", ""), "legacy_regtag": historic.get("RegTag", ""),
                "legacy_links": historic.get("Links", ""), "match_score": score, "year_match": str(year_match).lower(),
                "certificate_available_both": str(certificate_available).lower(), "certificate_match": str(certificate_match).lower(),
            })
    return register, candidates
