"""Bar chart comparing AI vs. human within-axis persona-pair correlations."""

from __future__ import annotations

import math
from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from result_analysis.charts.figure_utils import save_and_close
from result_analysis.charts.style import ANNOTATION_SIZE, LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.survey.constants import AXIS_PAIRS
from result_analysis.survey.stats import pearson_r_with_p


def _pair_correlation(
    frame: pd.DataFrame,
    *,
    persona_column: str,
    score_column: str,
    persona_a: str,
    persona_b: str,
) -> tuple[float, int]:
    """Compute the Pearson correlation between two personas' ratings on shared responses.

    Parameters:
        frame: Long-format ratings frame (human_means or ai_scores).
        persona_column: Column whose values name the two personas to compare.
        score_column: Numeric score column to correlate.
        persona_a: Name of the first persona.
        persona_b: Name of the second persona.

    Returns:
        Tuple ``(correlation, number_of_shared_responses)``. Correlation is
        NaN if there are fewer than 5 shared responses or either side has
        zero variance.
    """
    rows_a = frame[frame[persona_column] == persona_a].rename(
        columns={score_column: "score_a"}
    )
    rows_b = frame[frame[persona_column] == persona_b].rename(
        columns={score_column: "score_b"}
    )
    merged = rows_a[["question_id", "ai_model", "score_a"]].merge(
        rows_b[["question_id", "ai_model", "score_b"]],
        on=["question_id", "ai_model"],
    )
    correlation, _ = pearson_r_with_p(
        merged["score_a"].to_numpy(),
        merged["score_b"].to_numpy(),
        min_pairs=5,
    )
    return correlation, len(merged)


def compute_persona_pair_correlations(
    human_means: pd.DataFrame, ai_scores: pd.DataFrame
) -> pd.DataFrame:
    """Return per-axis AI and human pair correlations as a tidy frame.

    Parameters:
        human_means: Aggregated human means with ``human_persona`` and
            ``human_score`` columns.
        ai_scores: AI persona ratings with ``ai_persona`` and ``ai_score``
            columns.

    Returns:
        DataFrame with one row per axis and columns ``axis``, ``pair``,
        ``ai_r``, ``ai_n``, ``human_r``, ``human_n``.
    """
    rows: list[dict[str, float | str | int]] = []
    for axis_name, persona_a, persona_b in AXIS_PAIRS:
        ai_correlation, ai_pair_count = _pair_correlation(
            ai_scores,
            persona_column="ai_persona",
            score_column="ai_score",
            persona_a=persona_a,
            persona_b=persona_b,
        )
        human_correlation, human_pair_count = _pair_correlation(
            human_means,
            persona_column="human_persona",
            score_column="human_score",
            persona_a=persona_a,
            persona_b=persona_b,
        )
        rows.append(
            {
                "axis": axis_name,
                "pair": f"{persona_a} vs {persona_b}",
                "ai_r": ai_correlation,
                "ai_n": ai_pair_count,
                "human_r": human_correlation,
                "human_n": human_pair_count,
            }
        )
    return pd.DataFrame(rows)


def chart_persona_pair_opposition(
    human_means: pd.DataFrame,
    ai_scores: pd.DataFrame,
    output_path: Path,
) -> pd.DataFrame:
    """Save the AI-vs-human persona pair correlation bar chart.

    Each value axis contributes one pair (e.g. Libertarian vs. Collectivist).
    Negative correlations mean the two personas disagree across shared
    responses as expected.

    Parameters:
        human_means: Aggregated human means by persona and response.
        ai_scores: AI persona ratings by response.
        output_path: Destination PNG path.

    Returns:
        The pair correlations table produced by
        :func:`compute_persona_pair_correlations`, suitable for the summary
        builder.
    """
    pair_correlations = compute_persona_pair_correlations(human_means, ai_scores)

    fig, ax = plt.subplots(figsize=(10, 5))
    x_positions = np.arange(len(pair_correlations))
    bar_width = 0.36
    ax.bar(
        x_positions - bar_width / 2,
        pair_correlations["ai_r"].fillna(0),
        bar_width,
        label="AI personas",
        color="#5b8aa6",
        edgecolor="black",
        linewidth=0.6,
    )
    ax.bar(
        x_positions + bar_width / 2,
        pair_correlations["human_r"].fillna(0),
        bar_width,
        label="Human raters",
        color="#d97757",
        edgecolor="black",
        linewidth=0.6,
    )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(pair_correlations["pair"], rotation=15, ha="right")
    ax.set_ylabel(
        "Pearson correlation across shared responses", fontsize=LABEL_SIZE
    )
    ax.set_title(
        "Opposition between persona pairs: AI vs human raters\n"
        "(negative r = pairs disagree as expected)",
        fontsize=TITLE_SIZE,
    )
    ax.set_ylim(-1, 1)
    ax.legend(fontsize=TICK_SIZE)
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)

    for row_index, row in pair_correlations.iterrows():
        _annotate_bar(
            ax,
            x_positions[row_index] - bar_width / 2,
            row["ai_r"],
            row["ai_n"],
        )
        _annotate_bar(
            ax,
            x_positions[row_index] + bar_width / 2,
            row["human_r"],
            row["human_n"],
        )

    save_and_close(fig, output_path)
    return pair_correlations


def _annotate_bar(ax: plt.Axes, x_position: float, value: float, sample_size: int) -> None:
    """Draw a value/N annotation just above or below a bar tip.

    Parameters:
        ax: Axes hosting the bars.
        x_position: x-coordinate of the bar center.
        value: Bar height (NaN renders as ``n/a``).
        sample_size: Sample count to annotate alongside the value.

    Returns:
        Nothing.
    """
    if math.isnan(value):
        ax.text(x_position, 0.02, "n/a", ha="center", fontsize=ANNOTATION_SIZE)
        return
    y_offset = 0.04 if value >= 0 else -0.08
    ax.text(
        x_position,
        value + y_offset,
        f"{value:+.2f}\nN={sample_size}",
        ha="center",
        fontsize=ANNOTATION_SIZE,
    )
