"""Compute response-level persona scoring metrics and export JSON for llm-pluralism-web."""

from __future__ import annotations

import json
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
ALL_PERSONAS = [
    "Libertarian",
    "Collectivist",
    "Nationalist",
    "Globalist",
    "Tech Optimist",
    "Tech Sceptic",
    "Religious",
    "Secularist",
]

INPUT_CSV_PATH = Path("output/persona_responses.csv")
OUTPUT_JSON_PATH = Path("output/scripts/response_persona_scores.json")


def _to_float_or_none(value) -> float | None:
    """Convert a score-like value to float, returning None for invalid entries.

    Parameters
    ----------
    value:
        Raw score value from the input CSV.

    Returns
    -------
    float | None
        Parsed float score, or None when parsing is not possible.
    """
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_persona_score_dict(group_table: pd.DataFrame) -> dict[str, float | None]:
    """Build a complete persona score mapping (all 8 personas) for one response group.

    Parameters
    ----------
    group_table:
        Subset dataframe for a unique (question_id, source_model) response.

    Returns
    -------
    dict[str, float | None]
        Mapping from persona name to score or None.
    """
    score_by_persona: dict[str, float | None] = {persona_name: None for persona_name in ALL_PERSONAS}
    for _, row in group_table.iterrows():
        persona_name = str(row["persona_name"])
        if persona_name in score_by_persona:
            score_by_persona[persona_name] = _to_float_or_none(row["score"])
    return score_by_persona


def _active_scores(persona_scores: dict[str, float | None]) -> list[float]:
    """Extract available numeric scores for the active persona set.

    Parameters
    ----------
    persona_scores:
        Full persona score mapping for one response.

    Returns
    -------
    list[float]
        Numeric scores for active personas that are present and valid.
    """
    return [
        persona_scores[persona_name]
        for persona_name in sorted(ACTIVE_PERSONAS)
        if persona_scores.get(persona_name) is not None
    ]


def _warn_missing_active_personas(
    *,
    question_id: int,
    model_label: str,
    persona_scores: dict[str, float | None],
) -> None:
    """Print warnings for active personas that are missing scores.

    Parameters
    ----------
    question_id:
        Question identifier of the response.
    model_label:
        Model label for the response.
    persona_scores:
        Full persona score mapping for one response.
    """
    missing_personas = [
        persona_name
        for persona_name in sorted(ACTIVE_PERSONAS)
        if persona_scores.get(persona_name) is None
    ]
    for persona_name in missing_personas:
        print(
            f"Warning: missing active persona score for question_id={question_id}, "
            f"model={model_label}, persona_name={persona_name}"
        )


def _compute_metrics(scores: list[float]) -> tuple[float | None, float | None, float | None]:
    """Compute mean, discriminativeness (std), and bridging score from active persona scores.

    Parameters
    ----------
    scores:
        Numeric active persona scores for one response.

    Returns
    -------
    tuple[float | None, float | None, float | None]
        mean_score, discriminativeness, bridging_score.
    """
    if not scores:
        return None, None, None
    mean_score = float(np.mean(scores))
    discriminativeness = float(np.std(scores, ddof=0))
    bridging_score = float(mean_score - 0.5 * discriminativeness)
    return mean_score, discriminativeness, bridging_score


def _print_top_rows(
    *,
    title: str,
    rows: list[dict],
    metric_key: str,
    descending: bool,
) -> None:
    """Print top five rows for a metric.

    Parameters
    ----------
    title:
        Section heading to print.
    rows:
        Response rows with computed metrics.
    metric_key:
        Key name of the metric to rank by.
    descending:
        Whether to sort in descending order.
    """
    print(title)
    metric_rows = [row for row in rows if row.get(metric_key) is not None]
    metric_rows.sort(key=lambda row: row[metric_key], reverse=descending)
    for row in metric_rows[:5]:
        print(
            f"  question_id={row['question_id']}, model={row['model']}, "
            f"{metric_key}={row[metric_key]:.4f}"
        )


def main() -> None:
    """Load persona responses, compute response-level metrics, and export JSON plus summary."""
    response_table = pd.read_csv(INPUT_CSV_PATH)
    output_rows: list[dict] = []

    grouped = response_table.groupby(["question_id", "source_model"], sort=False)
    for (question_id, model_label), group_table in grouped:
        first_row = group_table.iloc[0]
        persona_scores = _build_persona_score_dict(group_table)
        _warn_missing_active_personas(
            question_id=int(question_id),
            model_label=str(model_label),
            persona_scores=persona_scores,
        )
        active_scores = _active_scores(persona_scores)
        mean_score, discriminativeness, bridging_score = _compute_metrics(active_scores)

        output_rows.append(
            {
                "question_id": int(first_row["question_id"]),
                "group_id": int(first_row["group_id"]),
                "group_name": str(first_row["group_name"]),
                "model": str(first_row["source_model"]),
                "prompt": str(first_row["question"]),
                "response_text": str(first_row["source_response"]),
                "persona_scores": persona_scores,
                "mean_score": mean_score,
                "discriminativeness": discriminativeness,
                "bridging_score": bridging_score,
            }
        )

    output_rows.sort(
        key=lambda row: row["bridging_score"] if row["bridging_score"] is not None else float("-inf"),
        reverse=True,
    )

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(output_rows, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    bridging_scores = [
        row["bridging_score"] for row in output_rows if row["bridging_score"] is not None
    ]
    mean_bridging_score = float(np.mean(bridging_scores)) if bridging_scores else float("nan")

    print(f"Total number of responses processed: {len(output_rows)}")
    print(f"Mean bridging score across all responses: {mean_bridging_score:.4f}")
    _print_top_rows(
        title="Top 5 most discriminating responses:",
        rows=output_rows,
        metric_key="discriminativeness",
        descending=True,
    )
    _print_top_rows(
        title="Top 5 least discriminating responses:",
        rows=output_rows,
        metric_key="discriminativeness",
        descending=False,
    )
    _print_top_rows(
        title="Top 5 highest bridging score responses:",
        rows=output_rows,
        metric_key="bridging_score",
        descending=True,
    )
    _print_top_rows(
        title="Top 5 lowest bridging score responses:",
        rows=output_rows,
        metric_key="bridging_score",
        descending=False,
    )


if __name__ == "__main__":
    main()
