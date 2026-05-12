"""Orchestrate the model-persona (LLM-as-rater) analysis stage."""

from __future__ import annotations

from pathlib import Path

from result_analysis.chart_common.io import read_csv_rows
from result_analysis.model_personas.charts.bridging import (
    chart_bridging_by_group,
    chart_bridging_by_model,
    chart_bridging_heatmap,
    chart_bridging_scores_ranked,
    chart_bridging_scores_ranked_trimmed,
    chart_lambda_comparison,
    chart_mean_vs_std_scatter,
    chart_mean_vs_std_scatter_interactive,
)
from result_analysis.model_personas.charts.persona import (
    chart_persona_correlation_heatmap,
    chart_persona_score_distributions,
    chart_persona_scores_by_model,
)
from result_analysis.model_personas.scoring import (
    compute_bridging_scores,
    compute_persona_correlations,
)


def generate_model_persona_analysis(
    *,
    persona_responses_csv: Path,
    bridging_scores_csv: Path,
    persona_correlations_csv: Path,
    bridging_score_lambda: float,
    output_dir: Path,
) -> None:
    """Compute model-persona scores then write all model-persona charts.

    Computes the bridging score and persona-correlation CSVs from
    ``persona_responses_csv`` and renders the full model-persona chart set
    into ``output_dir``.

    Parameters:
        persona_responses_csv: Path to ``persona_responses.csv``.
        bridging_scores_csv: Path for the bridging-score output CSV.
        persona_correlations_csv: Path for the persona-correlation output CSV.
        bridging_score_lambda: λ penalty for the primary bridging score column.
        output_dir: Directory where chart PNGs (and the output CSVs) are
            written; created if it does not exist.

    Returns:
        Nothing.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    compute_bridging_scores(
        input_csv=persona_responses_csv,
        output_csv=bridging_scores_csv,
        lambda_penalty=bridging_score_lambda,
    )
    compute_persona_correlations(
        input_csv=persona_responses_csv,
        output_csv=persona_correlations_csv,
    )

    bridging_rows = read_csv_rows(bridging_scores_csv)
    correlation_rows = read_csv_rows(persona_correlations_csv)
    persona_rating_rows = read_csv_rows(persona_responses_csv)

    chart_bridging_by_model(
        bridging_rows, output_dir / "bridging_scores_by_model.png"
    )
    chart_bridging_by_group(
        bridging_rows, output_dir / "bridging_scores_by_group.png"
    )
    chart_bridging_heatmap(
        bridging_rows, output_dir / "bridging_scores_by_model_and_group.png"
    )
    chart_persona_correlation_heatmap(
        correlation_rows, output_dir / "persona_correlations.png"
    )
    chart_mean_vs_std_scatter(
        bridging_rows, output_dir / "mean_vs_std_scatter.png"
    )
    chart_mean_vs_std_scatter_interactive(
        bridging_rows, output_dir / "mean_vs_std_scatter.html"
    )
    chart_persona_score_distributions(
        persona_rating_rows, output_dir / "persona_score_distributions.png"
    )
    chart_persona_scores_by_model(
        persona_rating_rows, output_dir / "persona_scores_by_model.png"
    )
    chart_bridging_scores_ranked(
        bridging_rows, output_dir / "bridging_scores_ranked.png"
    )
    chart_bridging_scores_ranked_trimmed(
        bridging_rows, output_dir / "bridging_scores_ranked_trimmed.png"
    )
    chart_lambda_comparison(
        bridging_rows, output_dir / "bridging_scores_lambda_comparison.png"
    )

    print(f"[persona_response_analyse] Wrote charts to {output_dir}")
