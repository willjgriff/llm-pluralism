"""Scatter of AI bridging score against persona-balanced mean human rating."""

from __future__ import annotations

import math
from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from result_analysis.charts.figure_utils import save_and_close
from result_analysis.charts.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.survey.stats import pearson_r_with_p

_MIN_PERSONA_GROUPS_FOR_FIT = 3
_MIN_POINTS_FOR_FIT = 5


def _persona_balanced_human_mean(humans: pd.DataFrame) -> pd.DataFrame:
    """Compute one mean human rating per response, weighting persona groups equally.

    First averages within each ``(question_id, ai_model, human_persona)``
    bucket, then averages those bucket means across personas so a single
    over-represented persona group cannot dominate the response-level mean.

    Parameters:
        humans: Per-rating frame with ``question_id``, ``ai_model``,
            ``human_persona``, ``score`` columns.

    Returns:
        DataFrame with columns ``question_id``, ``ai_model``,
        ``human_mean_balanced``, ``n_personas``.
    """
    persona_means = (
        humans.groupby(["question_id", "ai_model", "human_persona"])["score"]
        .mean()
        .reset_index()
    )
    return (
        persona_means.groupby(["question_id", "ai_model"])["score"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "human_mean_balanced", "count": "n_personas"})
    )


def chart_bridging_vs_human_mean(
    humans: pd.DataFrame, bridging: pd.DataFrame, output_path: Path
) -> None:
    """Save scatter of AI bridging score vs. persona-balanced human mean rating.

    Points are sized by the number of human persona groups contributing to the
    balanced mean and coloured by topic ``group_name``. A least-squares fit
    line and Pearson statistics are drawn over the subset of responses with
    ratings from at least :data:`_MIN_PERSONA_GROUPS_FOR_FIT` persona groups.

    Parameters:
        humans: Per-rating frame.
        bridging: Bridging score table (with ``ai_model`` already renamed from
            ``response_model`` by the loader).
        output_path: Destination PNG path.

    Returns:
        Nothing.
    """
    response_human_mean = _persona_balanced_human_mean(humans)
    merged = response_human_mean.merge(
        bridging[["question_id", "ai_model", "bridging_score", "group_name"]],
        on=["question_id", "ai_model"],
    )

    well_covered = merged[merged["n_personas"] >= _MIN_PERSONA_GROUPS_FOR_FIT]
    correlation, p_value = pearson_r_with_p(
        well_covered["bridging_score"].to_numpy(),
        well_covered["human_mean_balanced"].to_numpy(),
        min_pairs=_MIN_POINTS_FOR_FIT,
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    cmap = plt.colormaps["tab10"]
    sorted_groups = sorted(merged["group_name"].unique())
    for group_index, group_name in enumerate(sorted_groups):
        group_rows = merged[merged["group_name"] == group_name]
        ax.scatter(
            group_rows["bridging_score"],
            group_rows["human_mean_balanced"],
            s=20 + 12 * group_rows["n_personas"],
            alpha=0.7,
            edgecolor="black",
            linewidth=0.4,
            color=cmap(group_index),
            label=group_name,
        )

    if not math.isnan(correlation):
        x_values = well_covered["bridging_score"].to_numpy()
        y_values = well_covered["human_mean_balanced"].to_numpy()
        slope, intercept = np.polyfit(x_values, y_values, 1)
        x_fit = np.linspace(x_values.min(), x_values.max(), 50)
        ax.plot(
            x_fit,
            slope * x_fit + intercept,
            linestyle="--",
            color="black",
            linewidth=1,
            alpha=0.7,
            label=(
                f"OLS fit (r = {correlation:.2f}, p = {p_value:.3f}, "
                f"N = {len(well_covered)})"
            ),
        )

    ax.set_xlabel("AI bridging score (1–5)", fontsize=LABEL_SIZE)
    ax.set_ylabel(
        "Mean human rating, balanced across persona groups (1–5)", fontsize=LABEL_SIZE
    )
    ax.set_title(
        "Does the AI bridging score predict human consensus?\n"
        "(point size = number of human persona groups with ratings)",
        fontsize=TITLE_SIZE,
    )
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=TICK_SIZE - 1, framealpha=0.92)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    save_and_close(fig, output_path)
