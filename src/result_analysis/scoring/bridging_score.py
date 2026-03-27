"""Compute bridging scores from persona ratings."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean, pstdev

import config

BRIDGING_LAMBDA = 0.5
LAMBDA_VALUES: tuple[float, ...] = (0.25, 0.50, 0.75)


def _bridging_column_name(lambda_value: float) -> str:
    """Return CSV column name for a lambda value."""
    return f"bridging_score_{lambda_value:.2f}"


def compute_bridging_scores(
    *,
    input_csv: Path,
    output_csv: Path,
    lambda_penalty: float = BRIDGING_LAMBDA,
) -> dict[str, int]:
    print(f"[analyse] Computing bridging scores from {input_csv}")
    grouped_scores: dict[tuple[str, str, str, str, str], list[float]] = {}
    included_rows = 0

    with input_csv.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        for row in reader:
            persona_id = int(row["persona_id"])

            if persona_id not in config.ANALYSIS_PERSONA_IDS:
                continue

            score = float(row["score"].strip())
            question_id = row["question_id"].strip()
            group = (row.get("group") or row["group_id"]).strip()
            group_name = row["group_name"].strip()
            prompt = (row.get("prompt") or row["question"]).strip()
            response_model = (row.get("response_model") or row["source_model"]).strip()

            key = (question_id, group, group_name, prompt, response_model)
            grouped_scores.setdefault(key, []).append(score)
            included_rows += 1

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as output_file:
        fieldnames = [
            "question_id",
            "group",
            "group_name",
            "prompt",
            "response_model",
            "mean_score",
            "std_score",
            "bridging_score",
        ] + [_bridging_column_name(lambda_value) for lambda_value in LAMBDA_VALUES]
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()

        for (question_id, group, group_name, prompt, response_model), scores in sorted(grouped_scores.items()):
            mean_score = mean(scores)
            std_score = pstdev(scores) if len(scores) > 1 else 0.0
            bridging_score = mean_score - (lambda_penalty * std_score)
            row_data = {
                "question_id": question_id,
                "group": group,
                "group_name": group_name,
                "prompt": prompt,
                "response_model": response_model,
                "mean_score": f"{mean_score:.6f}",
                "std_score": f"{std_score:.6f}",
                "bridging_score": f"{bridging_score:.6f}",
            }
            for lambda_value in LAMBDA_VALUES:
                row_data[_bridging_column_name(lambda_value)] = (
                    f"{(mean_score - lambda_value * std_score):.6f}"
                )
            writer.writerow(row_data)

    print(
        f"[analyse] Wrote bridging scores to {output_csv} "
        f"(rows={len(grouped_scores)}, included_rows={included_rows})"
    )
    return {
        "included_rows": included_rows,
        "output_rows": len(grouped_scores),
    }
