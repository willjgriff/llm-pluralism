"""Charts derived from persona ratings and persona-correlation CSV rows."""

from __future__ import annotations

from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

import config
from result_analysis.charts.figure_utils import save_and_close
from result_analysis.charts.plot_utils import response_model_column, save_heatmap_with_colorbar
from result_analysis.charts.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE


def chart_persona_score_distributions(
    rows: list[dict[str, str]], output_path: Path
) -> None:
    """Boxplot of ``score`` distribution per ``ANALYSIS_PERSONA_IDS`` persona."""
    persona_ids = config.ANALYSIS_PERSONA_IDS
    scores_by_persona: dict[int, list[float]] = {pid: [] for pid in persona_ids}
    names_by_persona: dict[int, str] = {}

    for row in rows:
        persona_id = int(row["persona_id"])
        if persona_id not in scores_by_persona:
            continue
        scores_by_persona[persona_id].append(float(row["score"].strip()))
        names_by_persona[persona_id] = row["persona_name"].strip()

    persona_ids_present = [pid for pid in persona_ids if scores_by_persona[pid]]
    labels = [names_by_persona[pid] for pid in persona_ids_present]
    series = [scores_by_persona[pid] for pid in persona_ids_present]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(series, labels=labels, patch_artist=True)
    ax.set_title("Score Distribution by Persona", fontsize=TITLE_SIZE)
    ax.set_xlabel("Persona", fontsize=LABEL_SIZE)
    ax.set_ylabel("Score (1-5)", fontsize=LABEL_SIZE)
    ax.set_ylim(1, 5)
    ax.tick_params(axis="x", labelrotation=25, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)

    save_and_close(fig, output_path)


def chart_persona_scores_by_model(rows: list[dict[str, str]], output_path: Path) -> None:
    """Heatmap of mean persona score (1–5) per response model, averaged across prompts.

    Uses ``config.ANALYSIS_PERSONA_IDS`` for row order and persona names from the CSV.
    The response model column is ``response_model`` if present, otherwise ``source_model``.

    Parameters:
        rows: Rows from ``persona_responses.csv`` (or equivalent) with ``persona_id``,
            ``persona_name``, ``score``, and model columns.
        output_path: Path to write ``persona_scores_by_model.png``.

    Returns:
        Nothing. Writes the PNG file, or returns early if there is no data to plot.
    """
    persona_ids = config.ANALYSIS_PERSONA_IDS
    scores_by_persona_model: dict[tuple[int, str], list[float]] = {}
    name_by_id: dict[int, str] = {}
    models_set: set[str] = set()

    for row in rows:
        persona_id = int(row["persona_id"])
        if persona_id not in persona_ids:
            continue
        model = response_model_column(row)
        models_set.add(model)
        name_by_id[persona_id] = row["persona_name"].strip()
        key = (persona_id, model)
        scores_by_persona_model.setdefault(key, []).append(float(row["score"].strip()))

    models = sorted(models_set)
    row_labels = [name_by_id[pid] for pid in persona_ids if pid in name_by_id]
    if not models or not row_labels:
        return

    matrix = np.array(
        [
            [
                float(np.mean(scores_by_persona_model[(pid, model)]))
                for model in models
            ]
            for pid in persona_ids
            if pid in name_by_id
        ],
        dtype=float,
    )

    norm = colors.TwoSlopeNorm(vmin=1.0, vcenter=3.0, vmax=5.0)
    save_heatmap_with_colorbar(
        matrix=matrix,
        row_labels=row_labels,
        col_labels=models,
        norm=norm,
        title="Mean Persona Scores by Model",
        xlabel="Response Model",
        ylabel="Persona",
        output_path=output_path,
        figsize=(10, 6),
        aspect="auto",
        x_tick_rotation=25,
    )


def chart_persona_correlation_heatmap(
    rows: list[dict[str, str]], output_path: Path
) -> None:
    """Symmetric heatmap of pairwise Pearson correlations (from ``persona_correlations.csv``)."""
    persona_ids = sorted(
        {
            int(row["persona_a_id"])
            for row in rows
        }
        | {
            int(row["persona_b_id"])
            for row in rows
        }
    )
    name_by_id: dict[int, str] = {}
    for row in rows:
        name_by_id[int(row["persona_a_id"])] = row["persona_a_name"]
        name_by_id[int(row["persona_b_id"])] = row["persona_b_name"]

    index_by_id = {persona_id: i for i, persona_id in enumerate(persona_ids)}
    matrix = np.eye(len(persona_ids), dtype=float)
    for row in rows:
        a_id = int(row["persona_a_id"])
        b_id = int(row["persona_b_id"])
        corr = float(row["correlation"])
        i = index_by_id[a_id]
        j = index_by_id[b_id]
        matrix[i, j] = corr
        matrix[j, i] = corr

    labels = [name_by_id[persona_id] for persona_id in persona_ids]
    norm = colors.TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)

    save_heatmap_with_colorbar(
        matrix=matrix,
        row_labels=labels,
        col_labels=labels,
        norm=norm,
        title="Persona Rating Correlations",
        xlabel=None,
        ylabel=None,
        output_path=output_path,
        figsize=(8, 7),
        aspect="equal",
        x_tick_rotation=35,
    )
