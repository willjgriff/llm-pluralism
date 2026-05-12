"""Heatmap of Pearson agreement between each human persona and each AI persona."""

from __future__ import annotations

import math
from pathlib import Path

from result_analysis.chart_common import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from result_analysis.chart_common.figure_utils import save_and_close
from result_analysis.chart_common.style import ANNOTATION_SIZE, LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.human_survey.constants import PERSONA_ORDER
from result_analysis.human_survey.stats import pearson_r_with_p


def _human_personas_present(human_means: pd.DataFrame) -> list[str]:
    """Return canonical-order personas that appear in ``human_means``.

    Parameters:
        human_means: Aggregated human ratings with a ``human_persona`` column.

    Returns:
        Persona names from :data:`PERSONA_ORDER` filtered to those present.
    """
    present = set(human_means["human_persona"].unique())
    return [persona for persona in PERSONA_ORDER if persona in present]


def chart_human_ai_agreement_matrix(
    human_means: pd.DataFrame,
    ai_scores: pd.DataFrame,
    output_path: Path,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Save the human-vs-AI agreement heatmap and return its underlying matrices.

    For each ``(human_persona, ai_persona)`` cell, merges the two rating
    series on ``(question_id, ai_model)`` and computes a Pearson correlation
    when at least 5 paired observations exist with non-zero variance in both
    series.

    Diagonal cells where the two personas share a name are framed in black to
    highlight same-persona agreement.

    Parameters:
        human_means: Aggregated mean human ``human_score`` per
            ``(question_id, ai_model, human_persona)``.
        ai_scores: Per-response AI persona ratings with columns
            ``question_id``, ``ai_model``, ``ai_persona``, ``ai_score``.
        output_path: Destination PNG path.

    Returns:
        Tuple of ``(agreement_matrix, sample_counts, human_personas_used)``.
        Both matrices are shaped ``(len(human_personas_used), len(PERSONA_ORDER))``.
        Agreement cells are NaN where the correlation could not be computed.
    """
    human_personas = _human_personas_present(human_means)
    ai_personas = list(PERSONA_ORDER)

    agreement_matrix = np.full((len(human_personas), len(ai_personas)), np.nan)
    sample_counts = np.zeros_like(agreement_matrix, dtype=int)

    for human_index, human_persona in enumerate(human_personas):
        human_rows = human_means[human_means["human_persona"] == human_persona]
        for ai_index, ai_persona in enumerate(ai_personas):
            ai_rows = ai_scores[ai_scores["ai_persona"] == ai_persona]
            merged = human_rows.merge(ai_rows, on=["question_id", "ai_model"])
            sample_counts[human_index, ai_index] = len(merged)
            correlation, _ = pearson_r_with_p(
                merged["human_score"].to_numpy(),
                merged["ai_score"].to_numpy(),
                min_pairs=5,
            )
            agreement_matrix[human_index, ai_index] = correlation

    _render_agreement_heatmap(
        agreement_matrix=agreement_matrix,
        sample_counts=sample_counts,
        human_personas=human_personas,
        ai_personas=ai_personas,
        output_path=output_path,
    )
    return agreement_matrix, sample_counts, human_personas


def _render_agreement_heatmap(
    *,
    agreement_matrix: np.ndarray,
    sample_counts: np.ndarray,
    human_personas: list[str],
    ai_personas: list[str],
    output_path: Path,
) -> None:
    """Render the agreement heatmap with same-persona diagonal frames.

    Bespoke matplotlib rather than ``save_heatmap_with_colorbar`` because
    same-persona cells require black frames that the shared helper does not
    support.

    Parameters:
        agreement_matrix: Pearson r values; NaN where uncomputable.
        sample_counts: Pair counts per cell (annotated alongside r).
        human_personas: Row labels (y-axis).
        ai_personas: Column labels (x-axis).
        output_path: Destination PNG path.

    Returns:
        Nothing.
    """
    fig, ax = plt.subplots(figsize=(9, 6))
    image = ax.imshow(agreement_matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(ai_personas)))
    ax.set_xticklabels(ai_personas, rotation=30, ha="right")
    ax.set_yticks(range(len(human_personas)))
    ax.set_yticklabels(human_personas)
    ax.set_xlabel("AI persona", fontsize=LABEL_SIZE)
    ax.set_ylabel("Human persona group", fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)

    for human_index in range(len(human_personas)):
        for ai_index in range(len(ai_personas)):
            cell_value = agreement_matrix[human_index, ai_index]
            cell_count = int(sample_counts[human_index, ai_index])
            if math.isnan(cell_value):
                ax.text(
                    ai_index,
                    human_index,
                    f"—\n(N={cell_count})",
                    ha="center",
                    va="center",
                    fontsize=ANNOTATION_SIZE,
                    color="grey",
                )
                continue
            text_color = "white" if abs(cell_value) > 0.45 else "black"
            ax.text(
                ai_index,
                human_index,
                f"{cell_value:+.2f}\n(N={cell_count})",
                ha="center",
                va="center",
                color=text_color,
                fontsize=ANNOTATION_SIZE,
            )

    for human_index, human_persona in enumerate(human_personas):
        if human_persona in ai_personas:
            ai_index = ai_personas.index(human_persona)
            ax.add_patch(
                plt.Rectangle(
                    (ai_index - 0.5, human_index - 0.5),
                    1,
                    1,
                    fill=False,
                    edgecolor="black",
                    linewidth=2.5,
                )
            )

    ax.set_title(
        "Agreement between human and AI persona ratings\n"
        "(Pearson r across shared responses; diagonal = same-persona match)",
        fontsize=TITLE_SIZE,
    )
    colorbar = fig.colorbar(image, ax=ax, shrink=0.8)
    colorbar.set_label("Pearson correlation", fontsize=LABEL_SIZE)
    save_and_close(fig, output_path)
