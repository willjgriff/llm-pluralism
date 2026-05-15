"""Side-by-side human-group vs AI-persona mean ratings with 95% CIs."""

from __future__ import annotations

from pathlib import Path

from result_analysis.chart_common import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy.stats import t

from result_analysis.chart_common.figure_utils import (
    hide_top_right_spines,
    save_and_close,
)
from result_analysis.chart_common.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.human_survey.constants import (
    ANALYSIS_PERSONA_ORDER,
    SOCIETY_REASSIGNMENT_SUBTITLE,
    SURVEY_LOW_N_PARTICIPANTS,
)


def human_group_rating_stats(humans: pd.DataFrame) -> pd.DataFrame:
    """Mean human rating per persona group with 95% CI and participant counts.

    Excludes Centrist rows. Uses per-rating scores (not pre-aggregated means).

    Parameters:
        humans: Per-rating frame with ``human_persona``, ``score``,
            ``session_id``.

    Returns:
        DataFrame with columns ``persona``, ``mean``, ``std``, ``count``,
        ``sem``, ``ci95``, ``n_participants``.
    """
    frame = humans[humans["human_persona"] != "Centrist"].copy()
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce")
    grouped = (
        frame.groupby("human_persona")["score"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    grouped["sem"] = grouped["std"] / np.sqrt(grouped["count"].clip(lower=1))
    degrees_freedom = (grouped["count"] - 1).clip(lower=1)
    grouped["ci95"] = np.where(
        grouped["count"] >= 2,
        grouped["sem"] * t.ppf(0.975, degrees_freedom),
        0.0,
    )
    participant_counts = frame.groupby("human_persona")["session_id"].nunique()
    grouped["n_participants"] = grouped["human_persona"].map(participant_counts)
    return grouped.rename(columns={"human_persona": "persona"})


def ai_persona_rating_stats(persona_responses_raw: pd.DataFrame) -> pd.DataFrame:
    """Mean AI persona score per persona name with 95% CI across all rating rows.

    Parameters:
        persona_responses_raw: Raw ``persona_responses.csv`` frame with
            ``persona_name`` and ``score``.

    Returns:
        DataFrame with columns ``persona``, ``mean``, ``std``, ``count``,
        ``sem``, ``ci95``.
    """
    frame = persona_responses_raw.copy()
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce")
    grouped = (
        frame.groupby("persona_name")["score"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    grouped["sem"] = grouped["std"] / np.sqrt(grouped["count"].clip(lower=1))
    degrees_freedom = (grouped["count"] - 1).clip(lower=1)
    grouped["ci95"] = np.where(
        grouped["count"] >= 2,
        grouped["sem"] * t.ppf(0.975, degrees_freedom),
        0.0,
    )
    return grouped.rename(columns={"persona_name": "persona"})


def chart_human_ai_persona_mean_scores(
    humans: pd.DataFrame,
    persona_responses_raw: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save horizontal paired bars: human group mean vs AI persona mean per persona.

    Human bars are coloured by participant-count confidence; AI bars share one
    colour. Legend text includes the number of distinct evaluation responses
    scored in ``persona_responses_raw``.

    Parameters:
        humans: Per-rating survey frame (Centrist rows ignored).
        persona_responses_raw: Full persona responses CSV for AI aggregates.
        output_path: Destination PNG path.

    Returns:
        Nothing.
    """
    human_stats = human_group_rating_stats(humans).set_index("persona")
    ai_stats = ai_persona_rating_stats(persona_responses_raw).set_index("persona")
    chart_personas = list(ANALYSIS_PERSONA_ORDER)
    human_reindexed = human_stats.reindex(chart_personas)
    ai_reindexed = ai_stats.reindex(chart_personas)

    figure, axes = plt.subplots(figsize=(12, 6))
    hide_top_right_spines(axes)
    y_positions = np.arange(len(chart_personas))
    bar_half_width = 0.38

    human_colours: list[str] = []
    for persona_name in chart_personas:
        mean_value = human_reindexed.loc[persona_name, "mean"]
        if pd.isna(mean_value):
            human_colours.append("#dddddd")
        elif human_reindexed.loc[persona_name, "n_participants"] < SURVEY_LOW_N_PARTICIPANTS:
            human_colours.append("#b8d0b0")
        else:
            human_colours.append("#5a8a4a")

    axes.barh(
        y_positions - bar_half_width / 2,
        human_reindexed["mean"].fillna(0).to_numpy(),
        bar_half_width,
        xerr=human_reindexed["ci95"].fillna(0).to_numpy(),
        color=human_colours,
        edgecolor="black",
        linewidth=0.5,
        error_kw={"capsize": 3, "ecolor": "#333", "elinewidth": 1},
    )
    axes.barh(
        y_positions + bar_half_width / 2,
        ai_reindexed["mean"].fillna(0).to_numpy(),
        bar_half_width,
        xerr=ai_reindexed["ci95"].fillna(0).to_numpy(),
        color="#7a4eb5",
        edgecolor="black",
        linewidth=0.5,
        error_kw={"capsize": 3, "ecolor": "#333", "elinewidth": 1},
    )

    axes.set_yticks(y_positions)
    axes.set_yticklabels(chart_personas)
    axes.invert_yaxis()
    axes.set_xlim(1, 5)
    axes.axvline(3, color="#888", linestyle=":", linewidth=1)
    axes.set_xlabel(
        "Mean reasonableness score  (1 = strongly disagree, 5 = strongly agree)",
        fontsize=LABEL_SIZE,
    )
    axes.set_title(
        "Mean rating per persona: human group vs corresponding AI persona\n"
        f"{SOCIETY_REASSIGNMENT_SUBTITLE}",
        fontsize=TITLE_SIZE,
        pad=12,
    )
    axes.tick_params(axis="x", labelsize=TICK_SIZE)
    axes.tick_params(axis="y", labelsize=TICK_SIZE)

    for index, persona_name in enumerate(chart_personas):
        human_mean = human_reindexed.loc[persona_name, "mean"]
        if pd.notna(human_mean):
            participant_n = int(human_reindexed.loc[persona_name, "n_participants"])
            rating_n = int(human_reindexed.loc[persona_name, "count"])
            axes.text(
                human_mean + human_reindexed.loc[persona_name, "ci95"] + 0.05,
                index - bar_half_width / 2,
                f"{human_mean:.2f}  (N={participant_n}p, {rating_n}r)",
                va="center",
                fontsize=9,
            )
        else:
            axes.text(
                1.05,
                index - bar_half_width / 2,
                "no human data",
                va="center",
                fontsize=9,
                style="italic",
                color="#888",
            )

        ai_mean = ai_reindexed.loc[persona_name, "mean"]
        ai_rating_n = int(ai_reindexed.loc[persona_name, "count"])
        axes.text(
            ai_mean + ai_reindexed.loc[persona_name, "ci95"] + 0.05,
            index + bar_half_width / 2,
            f"{ai_mean:.2f}  (N={ai_rating_n}r)",
            va="center",
            fontsize=9,
        )

    n_evaluation_responses = persona_responses_raw.drop_duplicates(
        subset=["question_id", "source_model"]
    ).shape[0]

    human_legend_labels = {
        "#5a8a4a": (
            f"Human group (N ≥ {SURVEY_LOW_N_PARTICIPANTS} participants)"
        ),
        "#b8d0b0": (
            f"Human group (N < {SURVEY_LOW_N_PARTICIPANTS} participants, "
            "low confidence)"
        ),
        "#dddddd": "Human group (no data after reassignment)",
    }
    legend_handles: list[Patch] = []
    for bar_colour in dict.fromkeys(human_colours):
        label = human_legend_labels.get(bar_colour)
        if label is None:
            continue
        legend_handles.append(
            Patch(facecolor=bar_colour, edgecolor="black", label=label)
        )
    legend_handles.append(
        Patch(
            facecolor="#7a4eb5",
            edgecolor="black",
            label=(
                f"AI persona ({n_evaluation_responses} evaluation responses scored)"
            ),
        )
    )
    axes.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=2,
        frameon=False,
        fontsize=9,
    )

    save_and_close(
        figure,
        output_path,
        subplots_adjust_kwargs={"bottom": 0.18},
        savefig_kwargs={"bbox_inches": "tight"},
    )
