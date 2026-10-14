"""Protocolo auditável para reprodução histórica e validação de evidências."""

from __future__ import annotations

import csv
import random
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator


VALID_LABELS = ("favorable", "contrary", "insufficient", "not_applicable", "ambiguous")
PAIR_PATTERN = re.compile(r"\[\s*['\"](?P<feature>[^'\"]+)['\"]\s*,\s*['\"](?P<label>yes|no)['\"]\s*\]", re.IGNORECASE)


def parse_legacy_pairs(generated_text: str) -> list[dict[str, str]]:
    """Extrai pares explícitos de uma resposta LLaMA, sem transformá-los em escore.

    A resposta histórica mistura prompt e geração; por isso cada par deve continuar
    com status de revisão humana, e não pode ser tratado como rótulo científico final.
    """

    return [
        {"feature": match.group("feature").strip(), "legacy_label": match.group("label").lower()}
        for match in PAIR_PATTERN.finditer(str(generated_text))
    ]


def make_validation_rows(
    llama_csv: Path,
    output_csv: Path,
    *,
    sample_size: int = 80,
    seed: int = 2026,
) -> int:
    """Gera amostra determinística para avaliação humana das saídas históricas."""

    with llama_csv.open(encoding="latin1", newline="") as handle:
        rows = list(csv.DictReader(handle))
    candidates = []
    for report_index, row in enumerate(rows):
        for criterion, generated_text in row.items():
            if criterion == "Unnamed: 0" or not generated_text:
                continue
            pairs = parse_legacy_pairs(generated_text)
            candidates.append(
                {
                    "report_row": report_index,
                    "criterion_id": criterion.removesuffix("_criteria").replace("_", "."),
                    "legacy_pair_count": len(pairs),
                    "legacy_pairs": " | ".join(f"{x['feature']}={x['legacy_label']}" for x in pairs[:8]),
                    "generated_text_excerpt": generated_text.replace("\n", " ")[:1800],
                    "human_label": "",
                    "reviewer": "",
                    "review_notes": "",
                }
            )
    rng = random.Random(seed)
    sample = rng.sample(candidates, min(sample_size, len(candidates)))
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(sample[0]) if sample else []
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sample)
    return len(sample)


def summarize_legacy_pairs(llama_csv: Path) -> Counter[str]:
    with llama_csv.open(encoding="latin1", newline="") as handle:
        return Counter(pair["legacy_label"] for row in csv.DictReader(handle) for text in row.values() for pair in parse_legacy_pairs(text or ""))


def aggregate_validated_labels(rows: Iterable[dict[str, str]]) -> dict[str, int]:
    """Agrega apenas rótulos humanos/modelo já validados, sem pontuar ausência."""

    counts = Counter(row.get("human_label", "") for row in rows)
    invalid = set(counts) - set(VALID_LABELS) - {""}
    if invalid:
        raise ValueError(f"Rótulos inválidos: {sorted(invalid)}")
    return {label: counts[label] for label in VALID_LABELS}

