"""Box plot of human rating distribution per participant persona."""

from __future__ import annotations

from pathlib import Path

from result_analysis.chart_common import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from result_analysis.chart_common.figure_utils import save_and_close
from result_analysis.chart_common.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.human_survey.constants import (
    PERSONA_COLORS,
    PERSONA_ORDER,
    SOCIETY_REASSIGNMENT_SUBTITLE,
)

_JITTER_SEED = 42
_JITTER_SCALE = 0.07


def chart_human_score_distribution_by_persona(
    humans: pd.DataFrame, output_path: Path
) -> None:
    """Save a box-and-strip plot of human ratings grouped by participant persona.

    Each persona's box shows the IQR of ratings; individual ratings are
    overlaid as jittered scatter points. Sample sizes are annotated above the
    boxes.

    Parameters:
        humans: Per-rating frame with ``human_persona`` and ``score`` columns.
        output_path: Destination PNG path.

    Returns:
        Nothing.
    """
    persona_candidates = list(PERSONA_ORDER) + ["Centrist"]
    present_personas = set(humans["human_persona"].unique())
    persona_labels = [
        persona for persona in persona_candidates if persona in present_personas
    ]

    score_series_per_persona = [
        humans[humans["human_persona"] == persona]["score"].to_numpy()
        for persona in persona_labels
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    box_artist = ax.boxplot(
        score_series_per_persona,
        positions=range(len(persona_labels)),
        widths=0.55,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.5),
        showfliers=False,
    )
    for patch, persona in zip(box_artist["boxes"], persona_labels):
        patch.set_facecolor(PERSONA_COLORS.get(persona, "#888888"))
        patch.set_alpha(0.55)
        patch.set_edgecolor("black")

    random_generator = np.random.default_rng(_JITTER_SEED)
    for persona_index, persona in enumerate(persona_labels):
        persona_scores = humans[humans["human_persona"] == persona]["score"].to_numpy()
        jittered_x = random_generator.normal(
            loc=persona_index, scale=_JITTER_SCALE, size=len(persona_scores)
        )
        ax.scatter(jittered_x, persona_scores, alpha=0.35, s=14, color="black", zorder=3)

    ax.set_xticks(range(len(persona_labels)))
    ax.set_xticklabels(persona_labels, rotation=30, ha="right")
    ax.set_ylabel("Reasonableness rating (1–5)", fontsize=LABEL_SIZE)
    ax.set_title(
        "Distribution of human ratings by participant persona\n"
        f"(box = IQR, strip = individual ratings)  |  {SOCIETY_REASSIGNMENT_SUBTITLE}",
        fontsize=TITLE_SIZE,
    )
    ax.set_ylim(0.5, 5.5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.axhline(3, linestyle=":", linewidth=0.8, color="grey")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)

    for persona_index, persona in enumerate(persona_labels):
        sample_size = int((humans["human_persona"] == persona).sum())
        ax.text(
            persona_index,
            5.35,
            f"N={sample_size}",
            ha="center",
            va="bottom",
            fontsize=TICK_SIZE,
        )

    save_and_close(fig, output_path)
