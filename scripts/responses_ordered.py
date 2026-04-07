"""Order question responses by std and bridging score for persona categories."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ACTIVE_PERSONAS = {
    "Libertarian",
    "Collectivist",
    "Nationalist",
    "Globalist",
    "Tech Optimist",
    "Tech Sceptic",
}

GROUP_QUESTIONS = {
    "economic": [1, 2, 3, 4, 5, 6],
    "identity": [13, 14, 15],
    "technology": [10, 11, 12, 16, 17, 18],
    "society": [7, 8, 9],
}

INPUT_CSV_PATH = Path("output/persona_responses.csv")
OUTPUT_JSON_PATH = Path("output/scripts/responses_ordered.json")


def _import_config_module():
    """Import project config so model display names stay centralized."""
    try:
        import config  # type: ignore

        return config
    except ModuleNotFoundError:
        repository_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repository_root / "src"))
        import config  # type: ignore

        return config


config = _import_config_module()


def _to_float_or_none(value) -> float | None:
    """Convert a score value to float, returning None when not parseable.

    Parameters
    ----------
    value:
        Raw score value from the dataframe.

    Returns
    -------
    float | None
        Parsed numeric score, or None.
    """
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compute_metrics(scores: list[float]) -> tuple[float | None, float | None]:
    """Compute std and bridging score using the project formula.

    Parameters
    ----------
    scores:
        Numeric active-persona scores for a response.

    Returns
    -------
    tuple[float | None, float | None]
        std_score, bridging_score.
    """
    if not scores:
        return None, None
    mean_score = float(np.mean(scores))
    std_score = float(np.std(scores, ddof=0))
    bridging_score = float(mean_score - 0.5 * std_score)
    return std_score, bridging_score


def _build_response_rows(response_table: pd.DataFrame) -> list[dict]:
    """Aggregate persona rows into one row per (question_id, source_model).

    Parameters
    ----------
    response_table:
        Full persona responses table.

    Returns
    -------
    list[dict]
        Response rows with metadata, std_score, and bridging_score.
    """
    rows: list[dict] = []
    grouped = response_table.groupby(["question_id", "source_model"], sort=False)
    for (question_id, source_model), group_table in grouped:
        active_scores: list[float] = []
        for _, group_row in group_table.iterrows():
            persona_name = str(group_row["persona_name"])
            if persona_name in ACTIVE_PERSONAS:
                score_value = _to_float_or_none(group_row["score"])
                if score_value is not None:
                    active_scores.append(score_value)

        std_score, bridging_score = _compute_metrics(active_scores)
        first_row = group_table.iloc[0]
        model_label = str(source_model)
        rows.append(
            {
                "question_id": int(question_id),
                "model": model_label,
                "model_display_name": config.MODEL_DISPLAY_NAMES.get(model_label, model_label),
                "bridging_score": bridging_score,
                "std_score": std_score,
                "group_id": int(first_row["group_id"]),
                "group_name": str(first_row["group_name"]),
                "prompt_text": str(first_row["question"]),
                "response_text": str(first_row["source_response"]),
            }
        )
    return rows


def _order_rows(rows: list[dict], metric_key: str) -> list[dict]:
    """Return rows ordered by a metric descending with nulls last.

    Parameters
    ----------
    rows:
        Candidate rows to order.
    metric_key:
        Metric key to sort by.

    Returns
    -------
    list[dict]
        Sorted rows.
    """
    return sorted(
        rows,
        key=lambda row: row[metric_key] if row[metric_key] is not None else float("-inf"),
        reverse=True,
    )


def _build_output(rows: list[dict]) -> dict[str, dict[str, list[dict]]]:
    """Build category output payload with lists ordered by std and bridging score.

    Parameters
    ----------
    rows:
        All aggregated response rows.

    Returns
    -------
    dict
        JSON-ready category payload.
    """
    output_payload: dict[str, dict[str, list[dict]]] = {}
    for category_name, question_identifiers in GROUP_QUESTIONS.items():
        category_rows = [
            row for row in rows if int(row["question_id"]) in set(question_identifiers)
        ]
        output_payload[category_name] = {
            "ordered_by_std": _order_rows(category_rows, "std_score"),
            "ordered_by_bridging_score": _order_rows(category_rows, "bridging_score"),
        }
    return output_payload


def main() -> None:
    """Generate questions_ordered JSON from persona responses."""
    response_table = pd.read_csv(INPUT_CSV_PATH)
    aggregated_rows = _build_response_rows(response_table)
    output_payload = _build_output(aggregated_rows)

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(output_payload, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    print(f"Wrote questions ordered payload to {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
