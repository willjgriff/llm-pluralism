"""Heatmap of mean human rating per (persona, model)."""

from __future__ import annotations

from pathlib import Path

from result_analysis.chart_common import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colors

from result_analysis.chart_common.plot_utils import save_heatmap_with_colorbar
from result_analysis.chart_common.style import ANNOTATION_SIZE
from result_analysis.human_survey.constants import PERSONA_ORDER


def _personas_present(humans: pd.DataFrame) -> list[str]:
    """Return personas in canonical order that appear in ``humans``.

    Parameters:
        humans: DataFrame with a ``human_persona`` column.

    Returns:
        List of persona names from :data:`PERSONA_ORDER` (plus ``Centrist``)
        intersected with the personas actually present in the data.
    """
    candidates = list(PERSONA_ORDER) + ["Centrist"]
    present = set(humans["human_persona"].unique())
    return [persona for persona in candidates if persona in present]


def _ordered_model_short_labels(humans: pd.DataFrame) -> list[str]:
    """Return ``model_short`` labels in the order they appear in ``humans``.

    Parameters:
        humans: DataFrame with ``ai_model`` and ``model_short`` columns.

    Returns:
        Unique ``model_short`` labels preserving first-seen order.
    """
    return list(dict.fromkeys(humans["model_short"].tolist()))


def chart_human_persona_by_model_heatmap(
    humans: pd.DataFrame, output_path: Path
) -> None:
    """Save heatmap of mean human rating for each (persona, model) cell.

    Cells are annotated with the mean rating and sample count. Cells with no
    ratings render an em-dash. Colour scale runs 1 (critical, red) to 5
    (reasonable, blue) via ``RdBu``.

    Parameters:
        humans: Per-rating frame from :func:`load_survey_frames` (already
            filtered to non-repeat sessions).
        output_path: Destination PNG path.

    Returns:
        Nothing.
    """
    persona_labels = _personas_present(humans)
    model_labels = _ordered_model_short_labels(humans)

    mean_matrix = (
        humans.pivot_table(
            index="human_persona",
            columns="model_short",
            values="score",
            aggfunc="mean",
        )
        .reindex(index=persona_labels, columns=model_labels)
        .to_numpy(dtype=float)
    )
    count_matrix = (
        humans.pivot_table(
            index="human_persona",
            columns="model_short",
            values="score",
            aggfunc="count",
        )
        .reindex(index=persona_labels, columns=model_labels)
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    def annotate_with_counts(ax: plt.Axes, matrix: np.ndarray) -> None:
        for row_index in range(matrix.shape[0]):
            for column_index in range(matrix.shape[1]):
                cell_value = matrix[row_index, column_index]
                sample_size = int(count_matrix[row_index, column_index])
                if np.isnan(cell_value):
                    ax.text(
                        column_index,
                        row_index,
                        "—",
                        ha="center",
                        va="center",
                        fontsize=ANNOTATION_SIZE + 1,
                    )
                    continue
                text_color = "white" if abs(cell_value - 3) > 1.2 else "black"
                ax.text(
                    column_index,
                    row_index,
                    f"{cell_value:.2f}\n(N={sample_size})",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=ANNOTATION_SIZE,
                )

    norm = colors.TwoSlopeNorm(vmin=1.0, vcenter=3.0, vmax=5.0)
    save_heatmap_with_colorbar(
        matrix=mean_matrix,
        row_labels=persona_labels,
        col_labels=model_labels,
        norm=norm,
        title=(
            "Mean human rating by persona × model\n"
            "(red = lower / more critical, blue = higher / more reasonable)"
        ),
        xlabel=None,
        ylabel=None,
        output_path=output_path,
        figsize=(8, 6),
        aspect="auto",
        x_tick_rotation=0,
        cmap="RdBu",
        cell_annotator=annotate_with_counts,
        colorbar_label="Mean rating (1–5)",
    )
