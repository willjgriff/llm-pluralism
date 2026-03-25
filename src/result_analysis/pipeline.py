"""Orchestrate loading responses, scoring, CSV export, and charts."""

from __future__ import annotations

import shutil
from pathlib import Path

# Chart files produced by this pipeline (for optional copy to docs/images/).
_README_CHART_FILENAMES = (
    "pressure_level_yes_no_counts.png",
    "pressure_level_false_denial_rate.png",
    "pressure_level_false_denial_rate_by_model.png",
    "model_answer_change_when_pressured.png",
)

from result_analysis.charts import (
    build_false_denial_by_model_line_chart,
    build_false_denial_line_chart,
    build_model_neutral_yes_change_bar_chart,
    build_yes_no_bar_chart,
)
from result_analysis.csv_writes import (
    write_false_denial_by_model_csv,
    write_false_denial_csv,
    write_model_neutral_yes_change_csv,
    write_yes_no_counts_csv,
)
from result_analysis.scoring import (
    compute_false_denial_by_pressure_level,
    compute_false_denial_by_pressure_level_and_model,
    compute_neutral_yes_changed_when_pressured_by_model,
    count_yes_no_by_pressure_level,
    read_responses,
)


def _copy_charts_to_docs_images(*, output_dir: Path, docs_images_dir: Path) -> None:
    docs_images_dir.mkdir(parents=True, exist_ok=True)
    for chart_filename in _README_CHART_FILENAMES:
        source_path = output_dir / chart_filename
        if not source_path.is_file():
            continue
        destination_path = docs_images_dir / chart_filename
        shutil.copy2(source_path, destination_path)
        print(f"[analysis] Copied chart for README: {source_path} -> {destination_path}")


def run_yes_no_analysis(
    *,
    responses_csv: Path,
    output_dir: Path,
    copy_readme_images: bool = False,
    docs_images_dir: Path | None = None,
) -> None:
    """
    Score responses, write summary CSVs and charts under output_dir.

    If copy_readme_images is True, copy known chart PNGs to docs_images_dir
    (default: docs/images) for README embedding.
    """
    print(f"[analysis] Reading responses from: {responses_csv}")
    responses = read_responses(responses_csv)
    if not responses:
        raise ValueError(f"No rows found in {responses_csv}")
    print(f"[analysis] Loaded {len(responses)} responses")
    print("[analysis] Scoring responses into Yes/No/Other buckets")
    counts_by_level = count_yes_no_by_pressure_level(responses)

    sorted_pressure_levels = sorted(
        counts_by_level.keys(), key=lambda pressure_level: pressure_level[0]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[analysis] Found {len(sorted_pressure_levels)} pressure levels")
    summary_csv_path = write_yes_no_counts_csv(
        output_dir, sorted_pressure_levels, counts_by_level
    )
    yes_no_plot_path = build_yes_no_bar_chart(
        output_dir, sorted_pressure_levels, counts_by_level
    )
    print(f"[analysis] Analysis summary CSV: {summary_csv_path}")
    print(f"[analysis] Analysis plot: {yes_no_plot_path}")

    print("[analysis] Calculating false denial rate by pressure level")
    false_denial_summary, total_neutral_yes = compute_false_denial_by_pressure_level(
        responses
    )
    false_denial_levels = sorted(
        false_denial_summary.keys(), key=lambda pressure_level: pressure_level[0]
    )
    false_denial_csv_path = write_false_denial_csv(
        output_dir, false_denial_levels, false_denial_summary
    )
    false_denial_plot_path = build_false_denial_line_chart(
        output_dir, false_denial_levels, false_denial_summary, total_neutral_yes
    )
    print(f"[analysis] False denial CSV: {false_denial_csv_path}")
    print(f"[analysis] False denial plot: {false_denial_plot_path}")

    print("[analysis] Calculating false denial rate by pressure level and model")
    false_denial_by_model_summary, total_neutral_yes_by_model = (
        compute_false_denial_by_pressure_level_and_model(responses)
    )
    sorted_models = sorted(
        {summary_key[2] for summary_key in false_denial_by_model_summary.keys()}
    )
    by_model_csv_path = write_false_denial_by_model_csv(
        output_dir,
        false_denial_levels,
        sorted_models,
        false_denial_by_model_summary,
    )
    by_model_plot_path = build_false_denial_by_model_line_chart(
        output_dir,
        false_denial_levels,
        sorted_models,
        false_denial_by_model_summary,
        total_neutral_yes_by_model,
    )
    print(f"[analysis] Per-model false denial CSV: {by_model_csv_path}")
    print(f"[analysis] Per-model false denial plot: {by_model_plot_path}")

    print(
        "[analysis] Calculating neutral-Yes change rate when pressured (by model)"
    )
    change_summary_by_model = compute_neutral_yes_changed_when_pressured_by_model(
        responses
    )
    sorted_models_for_change = sorted(change_summary_by_model.keys())
    if sorted_models_for_change:
        change_csv_path = write_model_neutral_yes_change_csv(
            output_dir, sorted_models_for_change, change_summary_by_model
        )
        change_plot_path = build_model_neutral_yes_change_bar_chart(
            output_dir, sorted_models_for_change, change_summary_by_model
        )
        print(f"[analysis] Model neutral-Yes change CSV: {change_csv_path}")
        print(f"[analysis] Model neutral-Yes change plot: {change_plot_path}")
    else:
        print(
            "[analysis] Skipping model neutral-Yes change chart (no questions with "
            "neutral 'Yes' in the data)."
        )

    if copy_readme_images:
        readme_docs_dir = docs_images_dir if docs_images_dir is not None else Path(
            "docs/images"
        )
        print(f"[analysis] Copying charts to {readme_docs_dir} for README embedding")
        _copy_charts_to_docs_images(output_dir=output_dir, docs_images_dir=readme_docs_dir)
