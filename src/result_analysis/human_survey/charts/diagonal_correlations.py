"""Horizontal bar chart of same-axis human vs AI persona correlations."""

from __future__ import annotations

from pathlib import Path

from result_analysis.chart_common import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from result_analysis.chart_common.figure_utils import (
    hide_top_right_spines,
    save_and_close,
)
from result_analysis.chart_common.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.human_survey.constants import (
    SOCIETY_REASSIGNMENT_SUBTITLE,
    SURVEY_LOW_N_RESPONSES,
)


def chart_same_axis_diagonal_correlations(
    correlation_frame: pd.DataFrame,
    count_frame: pd.DataFrame,
    humans: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save a bar chart of diagonal (same-persona) Pearson r, sorted descending.

    Bar colour reflects whether the cell has at least ``SURVEY_LOW_N_RESPONSES``
    paired observations. Annotations include response N and participant N per
    human persona group.

    Parameters:
        correlation_frame: Matrix indexed by human persona with columns
            including each AI persona name on the diagonal.
        count_frame: Same index/columns as ``correlation_frame``; integer N per
            cell.
        humans: Full per-rating frame (used only to count participants per
            human persona, excluding Centrist).
        output_path: Destination PNG path.

    Returns:
        Nothing.
    """
    validation_humans = humans[humans["human_persona"] != "Centrist"]
    participant_counts = validation_humans.groupby("human_persona")[
        "session_id"
    ].nunique()

    diagonal_entries: list[tuple[str, float, int]] = []
    for persona_name in correlation_frame.index:
        if persona_name not in correlation_frame.columns:
            continue
        correlation_value = correlation_frame.loc[persona_name, persona_name]
        if np.isnan(correlation_value):
            continue
        response_n = int(count_frame.loc[persona_name, persona_name])
        diagonal_entries.append(
            (persona_name, float(correlation_value), response_n)
        )

    if not diagonal_entries:
        figure, axes = plt.subplots(figsize=(9, 5.5))
        axes.text(
            0.5,
            0.5,
            "No same-axis correlations to plot.",
            ha="center",
            va="center",
            transform=axes.transAxes,
        )
        axes.axis("off")
        save_and_close(figure, output_path)
        return

    diagonal_entries.sort(key=lambda item: item[1], reverse=True)
    persona_names, correlation_values, response_counts = zip(*diagonal_entries)
    bar_colours = [
        "#9e9e9e" if response_n < SURVEY_LOW_N_RESPONSES else "#3a6ea5"
        for response_n in response_counts
    ]

    figure, axes = plt.subplots(figsize=(9, 5.5))
    hide_top_right_spines(axes)
    axes.barh(
        list(persona_names),
        list(correlation_values),
        color=bar_colours,
        edgecolor="black",
        linewidth=0.5,
    )
    axes.axvline(0, color="black", linewidth=0.8)
    axes.set_xlabel(
        "Pearson r  (human-group mean rating  vs  AI-persona score)",
        fontsize=LABEL_SIZE,
    )
    axes.set_title(
        "Same-axis correlation: human persona group vs corresponding AI persona\n"
        f"{SOCIETY_REASSIGNMENT_SUBTITLE}",
        fontsize=TITLE_SIZE,
        pad=12,
    )
    axes.set_xlim(-0.2, 0.6)
    axes.tick_params(axis="x", labelsize=TICK_SIZE)
    axes.tick_params(axis="y", labelsize=TICK_SIZE)

    for row_index, (persona_name, correlation_value, response_n) in enumerate(
        zip(persona_names, correlation_values, response_counts)
    ):
        participant_n = int(participant_counts.get(persona_name, 0))
        x_anchor = max(correlation_value, 0.0) + 0.012
        axes.text(
            x_anchor,
            row_index,
            f"r = {correlation_value:+.2f}   (N={response_n} responses, "
            f"{participant_n} participants)",
            va="center",
            ha="left",
            fontsize=10,
        )

    axes.invert_yaxis()

    save_and_close(
        figure,
        output_path,
        savefig_kwargs={"bbox_inches": "tight"},
    )
