"""Orchestrate the survey (human-vs-AI) analysis stage."""

from __future__ import annotations

from pathlib import Path

from result_analysis.survey.charts import (
    chart_bridging_vs_human_mean,
    chart_human_ai_agreement_matrix,
    chart_human_persona_by_model_heatmap,
    chart_human_score_distribution_by_persona,
    chart_persona_pair_opposition,
)
from result_analysis.survey.loaders import load_survey_frames
from result_analysis.survey.summary import build_summary_table, write_summary_table


def generate_survey_analysis(
    *,
    sessions_csv: Path,
    ratings_csv: Path,
    persona_responses_csv: Path,
    bridging_scores_csv: Path,
    output_dir: Path,
) -> None:
    """Run the full survey analysis pipeline and write charts + summary table.

    Loads human ratings (sessions + ratings export), AI persona ratings, and
    bridging scores; generates five charts comparing human and AI evaluations;
    and writes a per-axis summary table as CSV and Markdown.

    Parameters:
        sessions_csv: Path to ``web_export_sessions.csv``.
        ratings_csv: Path to ``web_export_ratings.csv``.
        persona_responses_csv: Path to AI persona ratings CSV.
        bridging_scores_csv: Path to bridging-score CSV (produced by the
            ``analyse`` stage).
        output_dir: Directory to write charts and summary files into. Created
            if it does not exist.

    Returns:
        Nothing.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    frames = load_survey_frames(
        sessions_csv=sessions_csv,
        ratings_csv=ratings_csv,
        persona_responses_csv=persona_responses_csv,
        bridging_scores_csv=bridging_scores_csv,
    )
    print(
        f"[survey_analyse] Loaded {len(frames.humans)} non-repeat ratings across "
        f"{frames.humans['session_id'].nunique()} sessions"
    )

    chart_human_persona_by_model_heatmap(
        frames.humans, output_dir / "human_persona_by_model_heatmap.png"
    )
    chart_human_score_distribution_by_persona(
        frames.humans, output_dir / "human_score_distribution_by_persona.png"
    )
    chart_bridging_vs_human_mean(
        frames.humans, frames.bridging, output_dir / "bridging_vs_human_mean.png"
    )
    agreement_matrix, sample_counts, human_personas = chart_human_ai_agreement_matrix(
        frames.human_means,
        frames.ai_scores,
        output_dir / "ai_human_agreement_matrix.png",
    )
    pair_correlations = chart_persona_pair_opposition(
        frames.human_means,
        frames.ai_scores,
        output_dir / "persona_pair_opposition_ai_vs_human.png",
    )

    summary_table = build_summary_table(
        pair_correlations, agreement_matrix, sample_counts, human_personas
    )
    csv_path, markdown_path = write_summary_table(summary_table, output_dir)

    print(f"[survey_analyse] Wrote charts and summary to {output_dir}")
    print(f"[survey_analyse] Summary CSV -> {csv_path}")
    print(f"[survey_analyse] Summary Markdown -> {markdown_path}")
