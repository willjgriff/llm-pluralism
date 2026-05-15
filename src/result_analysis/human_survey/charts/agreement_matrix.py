"""Full human-group × AI-persona Pearson correlation heatmap (validation parity)."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from scipy.stats import pearsonr

from result_analysis.chart_common import _backend  # noqa: F401
from result_analysis.chart_common.figure_utils import save_and_close
from result_analysis.chart_common.style import ANNOTATION_SIZE, LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.human_survey.constants import (
    PERSONA_ORDER,
    SOCIETY_REASSIGNMENT_SUBTITLE,
    SURVEY_LOW_N_RESPONSES,
)


def _humans_validation_subset(humans: pd.DataFrame) -> pd.DataFrame:
    """Return ratings excluding Centrist participants (no AI Centrist to compare).

    Parameters:
        humans: Per-rating frame with ``human_persona`` column.

    Returns:
        Copy of ``humans`` without rows where ``human_persona`` is ``Centrist``.
    """
    return humans[humans["human_persona"] != "Centrist"].copy()


def compute_human_ai_correlation_matrices(
    humans: pd.DataFrame, ai_scores: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build human-persona × AI-persona Pearson r matrix and per-cell N (que-pasa parity).

    Merges human group means per ``(question_id, ai_model)`` with AI persona
    scores on the same keys. Correlation is computed only when there are at
    least 3 paired rows and both sides have positive variance (same rule as
    the standalone validation script).

    Parameters:
        humans: Per-rating frame from :func:`load_survey_frames`.
        ai_scores: Frame with ``question_id``, ``ai_model``, ``ai_persona``,
            ``ai_score``.

    Returns:
        Tuple ``(correlation_df, count_df)`` with index = human persona groups
        present (excluding Centrist), columns = :data:`PERSONA_ORDER` AI
        personas, values Pearson r or NaN, and integer counts per cell.
    """
    df = _humans_validation_subset(humans)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    human_means = (
        df.groupby(["question_id", "ai_model", "human_persona"])
        .agg(human_mean=("score", "mean"))
        .reset_index()
    )
    ai = ai_scores.copy()
    ai["ai_score"] = pd.to_numeric(ai["ai_score"], errors="coerce")

    row_personas = sorted(
        df["human_persona"].unique(),
        key=lambda persona_name: PERSONA_ORDER.index(persona_name),
    )
    correlation_frame = pd.DataFrame(
        index=row_personas, columns=list(PERSONA_ORDER), dtype=float
    )
    count_frame = pd.DataFrame(
        index=row_personas, columns=list(PERSONA_ORDER), dtype=int
    )

    for human_persona in row_personas:
        human_slice = human_means.loc[
            human_means["human_persona"] == human_persona,
            ["question_id", "ai_model", "human_mean"],
        ]
        for ai_persona in PERSONA_ORDER:
            ai_slice = ai.loc[
                ai["ai_persona"] == ai_persona,
                ["question_id", "ai_model", "ai_score"],
            ]
            merged = human_slice.merge(
                ai_slice, on=["question_id", "ai_model"], how="inner"
            )
            pair_count = len(merged)
            count_frame.loc[human_persona, ai_persona] = pair_count
            if (
                pair_count >= 3
                and merged["human_mean"].std() > 0
                and merged["ai_score"].std() > 0
            ):
                correlation_value, _ = pearsonr(
                    merged["human_mean"].to_numpy(),
                    merged["ai_score"].to_numpy(),
                )
                correlation_frame.loc[human_persona, ai_persona] = float(
                    correlation_value
                )
            else:
                correlation_frame.loc[human_persona, ai_persona] = math.nan

    return correlation_frame, count_frame


def chart_human_ai_agreement_matrix(
    humans: pd.DataFrame,
    ai_scores: pd.DataFrame,
    output_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Save the full validation heatmap and return correlation + count matrices.

    Parameters:
        humans: Per-rating frame from :func:`load_survey_frames`.
        ai_scores: AI persona ratings aligned on ``question_id`` / ``ai_model``.
        output_path: Destination PNG path (typically
            ``ai_human_agreement_matrix.png``).

    Returns:
        ``(correlation_df, count_df)`` for reuse by the diagonal bar chart.
    """
    correlation_frame, count_frame = compute_human_ai_correlation_matrices(
        humans, ai_scores
    )
    _render_full_agreement_heatmap(
        correlation_frame=correlation_frame,
        count_frame=count_frame,
        output_path=output_path,
    )
    return correlation_frame, count_frame


def _render_full_agreement_heatmap(
    *,
    correlation_frame: pd.DataFrame,
    count_frame: pd.DataFrame,
    output_path: Path,
) -> None:
    """Draw the RdBu heatmap with diagonal frames, annotations, and footnote."""
    matrix = correlation_frame.values.astype(float)
    figure, axes = plt.subplots(figsize=(11, 7))
    colour_map = plt.cm.RdBu_r
    normalizer = mpl.colors.Normalize(vmin=-0.75, vmax=0.75)
    masked = np.ma.masked_invalid(matrix)
    image = axes.imshow(masked, cmap=colour_map, norm=normalizer, aspect="auto")

    for row_index, human_persona in enumerate(correlation_frame.index):
        if human_persona in PERSONA_ORDER:
            column_index = PERSONA_ORDER.index(human_persona)
            axes.add_patch(
                Rectangle(
                    (column_index - 0.5, row_index - 0.5),
                    1,
                    1,
                    fill=False,
                    edgecolor="black",
                    linewidth=2.5,
                )
            )

    for row_index, human_persona in enumerate(correlation_frame.index):
        for column_index, ai_persona in enumerate(PERSONA_ORDER):
            cell_value = matrix[row_index, column_index]
            cell_count = int(count_frame.loc[human_persona, ai_persona])
            if math.isnan(cell_value):
                axes.text(
                    column_index,
                    row_index,
                    "no data",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="#444",
                    style="italic",
                )
            else:
                text_color = "white" if abs(cell_value) > 0.45 else "black"
                low_n_marker = (
                    "*" if cell_count < SURVEY_LOW_N_RESPONSES else ""
                )
                axes.text(
                    column_index,
                    row_index,
                    f"{cell_value:+.2f}{low_n_marker}\n(N={cell_count})",
                    ha="center",
                    va="center",
                    fontsize=ANNOTATION_SIZE,
                    color=text_color,
                )

    axes.set_xticks(range(len(PERSONA_ORDER)))
    axes.set_xticklabels(list(PERSONA_ORDER), rotation=30, ha="right")
    axes.set_yticks(range(len(correlation_frame.index)))
    axes.set_yticklabels(list(correlation_frame.index))
    axes.set_xlabel("AI persona", fontsize=LABEL_SIZE)
    axes.set_ylabel("Human persona group (analysis axis)", fontsize=LABEL_SIZE)
    axes.tick_params(axis="x", labelsize=TICK_SIZE)
    axes.tick_params(axis="y", labelsize=TICK_SIZE)
    axes.set_title(
        "Human persona group vs AI persona: Pearson r across rated responses\n"
        f"Bordered cells = same-axis match  |  {SOCIETY_REASSIGNMENT_SUBTITLE}",
        fontsize=TITLE_SIZE,
        pad=12,
    )

    colour_bar = plt.colorbar(image, ax=axes, shrink=0.85)
    colour_bar.set_label("Pearson r", fontsize=LABEL_SIZE)

    footnote_text = (
        f"* cells with N < {SURVEY_LOW_N_RESPONSES} responses are less reliable; "
        "interpret with caution"
    )

    def _draw_footnote(fig: plt.Figure) -> None:
        """Place the low-N footnote in figure coordinates below the subplot grid."""
        fig.text(
            0.5,
            0.055,
            footnote_text,
            ha="center",
            va="bottom",
            fontsize=9,
            style="italic",
            color="#555",
        )

    save_and_close(
        figure,
        output_path,
        tight_layout_rect=(0.02, 0.16, 0.98, 0.96),
        after_tight_layout=_draw_footnote,
        subplots_adjust_kwargs={"bottom": 0.20},
    )
