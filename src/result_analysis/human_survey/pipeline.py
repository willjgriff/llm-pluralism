"""Orchestrate the survey (human-vs-AI) analysis stage."""

from __future__ import annotations

from pathlib import Path

from result_analysis.human_survey.charts import (
    chart_human_ai_agreement_matrix,
    chart_human_ai_persona_mean_scores,
    chart_human_score_distribution_by_persona,
    chart_same_axis_diagonal_correlations,
)
from result_analysis.human_survey.loaders import load_survey_frames


def generate_survey_analysis(
    *,
    sessions_csv: Path,
    ratings_csv: Path,
    persona_responses_csv: Path,
    output_dir: Path,
) -> None:
    """Run the full survey analysis pipeline and write charts.

    Loads human ratings (sessions + ratings export) and AI persona ratings;
    writes four PNGs under ``output_dir``: distribution, full agreement
    heatmap, same-axis diagonal correlations, and human vs AI mean scores.

    Parameters:
        sessions_csv: Path to ``survey_responses_sessions.csv``.
        ratings_csv: Path to ``survey_responses_ratings.csv``.
        persona_responses_csv: Path to AI persona ratings CSV.
        output_dir: Directory to write charts into. Created if it does not exist.

    Returns:
        Nothing.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = load_survey_frames(
        sessions_csv=sessions_csv,
        ratings_csv=ratings_csv,
        persona_responses_csv=persona_responses_csv,
    )
    print(
        f"[survey_response_analyse] Loaded {len(frames.humans)} ratings "
        f"across {frames.humans['session_id'].nunique()} sessions"
    )

    chart_human_score_distribution_by_persona(
        frames.humans, output_dir / "human_score_distribution_by_persona.png"
    )
    correlation_frame, count_frame = chart_human_ai_agreement_matrix(
        frames.humans,
        frames.ai_scores,
        output_dir / "ai_human_agreement_matrix.png",
    )
    chart_same_axis_diagonal_correlations(
        correlation_frame,
        count_frame,
        frames.humans,
        output_dir / "same_axis_human_ai_persona_correlations.png",
    )
    chart_human_ai_persona_mean_scores(
        frames.humans,
        frames.persona_responses_raw,
        output_dir / "human_vs_ai_persona_mean_scores.png",
    )

    print(f"[survey_response_analyse] Wrote charts to {output_dir}")
