"""Orchestrate loading CSV inputs and writing all analysis chart PNGs."""

from __future__ import annotations

from pathlib import Path

from result_analysis.charts.bridging import (
    chart_bridging_by_group,
    chart_bridging_by_model,
    chart_bridging_heatmap,
    chart_bridging_scores_ranked,
    chart_lambda_comparison,
    chart_mean_vs_std_scatter,
)
from result_analysis.charts.io import read_csv_rows
from result_analysis.charts.persona import (
    chart_persona_correlation_heatmap,
    chart_persona_score_distributions,
    chart_persona_scores_by_model,
)


def generate_analysis_charts(
    *,
    bridging_scores_csv: Path,
    persona_correlations_csv: Path,
    persona_ratings_csv: Path,
    output_dir: Path,
) -> None:
    """Read analysis CSVs and write the full set of chart images to ``output_dir``."""
    output_dir.mkdir(parents=True, exist_ok=True)

    bridging_rows = read_csv_rows(bridging_scores_csv)
    correlation_rows = read_csv_rows(persona_correlations_csv)
    persona_rating_rows = read_csv_rows(persona_ratings_csv)

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
    chart_persona_score_distributions(
        persona_rating_rows, output_dir / "persona_score_distributions.png"
    )
    chart_persona_scores_by_model(
        persona_rating_rows, output_dir / "persona_scores_by_model.png"
    )
    chart_bridging_scores_ranked(
        bridging_rows, output_dir / "bridging_scores_ranked.png"
    )
    chart_lambda_comparison(
        bridging_rows, output_dir / "bridging_scores_lambda_comparison.png"
    )

    print(f"[analyse] Wrote charts to {output_dir}")
