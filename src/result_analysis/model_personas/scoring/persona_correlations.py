"""Compute pairwise Pearson correlations between persona rating vectors."""

from __future__ import annotations

import csv
from itertools import combinations
from pathlib import Path

import numpy as np

import config

OUTPUT_COLUMNS = [
    "persona_a_id",
    "persona_a_name",
    "persona_b_id",
    "persona_b_name",
    "correlation",
]


def compute_persona_correlations(*, input_csv: Path, output_csv: Path) -> dict[str, int]:
    print(f"[analyse] Computing persona correlations from {input_csv}")

    persona_ids = config.ANALYSIS_PERSONA_IDS
    scores_by_persona: dict[int, dict[tuple[str, str], float]] = {
        persona_id: {} for persona_id in persona_ids
    }
    names_by_persona: dict[int, str] = {}

    with input_csv.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            persona_id = int(row["persona_id"])
            if persona_id not in persona_ids:
                continue

            response_model = row["source_model"].strip()
            response_key = (row["question_id"].strip(), response_model)
            scores_by_persona[persona_id][response_key] = float(row["score"].strip())
            names_by_persona[persona_id] = row["persona_name"].strip()

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with output_csv.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for persona_a_id, persona_b_id in combinations(persona_ids, 2):
            persona_a_scores = scores_by_persona[persona_a_id]
            persona_b_scores = scores_by_persona[persona_b_id]
            common_keys = sorted(set(persona_a_scores) & set(persona_b_scores))
            a_vec = np.array([persona_a_scores[key] for key in common_keys], dtype=float)
            b_vec = np.array([persona_b_scores[key] for key in common_keys], dtype=float)
            corr = float(np.corrcoef(a_vec, b_vec)[0, 1])

            writer.writerow(
                {
                    "persona_a_id": persona_a_id,
                    "persona_a_name": names_by_persona[persona_a_id],
                    "persona_b_id": persona_b_id,
                    "persona_b_name": names_by_persona[persona_b_id],
                    "correlation": f"{corr:.3f}",
                }
            )
            row_count += 1

    print(f"[analyse] Wrote persona correlations to {output_csv} (rows={row_count})")
    return {"output_rows": row_count}
