"""Load and join the four CSVs used by survey (human-vs-AI) analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

import config
from result_analysis.charts.plot_utils import display_model_name


@dataclass(frozen=True)
class SurveyFrames:
    """Cleaned and joined frames used across every survey chart.

    Attributes:
        humans: One row per human rating with session persona joined in,
            ``is_repeat`` rows already filtered out. Columns include
            ``session_id``, ``question_id``, ``ai_model``, ``model_short``,
            ``human_persona``, ``score``.
        human_means: Mean human ``score`` per ``(question_id, ai_model,
            human_persona)`` with sample count in ``n_humans``. Score column
            is renamed to ``human_score``.
        ai_scores: Per-response AI persona ratings with columns
            ``question_id``, ``ai_model``, ``ai_persona``, ``ai_score``,
            ``group_name``.
        bridging: Bridging score table with ``ai_model`` column (renamed from
            ``response_model``), ``bridging_score`` and ``group_name``.
    """

    humans: pd.DataFrame
    human_means: pd.DataFrame
    ai_scores: pd.DataFrame
    bridging: pd.DataFrame


def load_survey_frames(
    *,
    sessions_csv: Path,
    ratings_csv: Path,
    persona_responses_csv: Path,
    bridging_scores_csv: Path,
) -> SurveyFrames:
    """Read the four input CSVs and return cleaned, joined dataframes.

    Parameters:
        sessions_csv: Path to ``web_export_sessions.csv``.
        ratings_csv: Path to ``web_export_ratings.csv``.
        persona_responses_csv: Path to AI persona ratings CSV (e.g.
            ``persona_responses.csv``).
        bridging_scores_csv: Path to per-response bridging score CSV.

    Returns:
        A :class:`SurveyFrames` with humans, human_means, ai_scores, bridging.
    """
    ratings = pd.read_csv(ratings_csv)
    sessions = pd.read_csv(sessions_csv)
    ai_responses = pd.read_csv(persona_responses_csv)
    bridging = pd.read_csv(bridging_scores_csv)

    humans = ratings.merge(
        sessions[["id", "primary_persona", "is_repeat"]],
        left_on="session_id",
        right_on="id",
        suffixes=("", "_session"),
    )
    humans = humans[~humans["is_repeat"]].copy()
    humans = humans.rename(
        columns={"primary_persona": "human_persona", "model": "ai_model"}
    )
    humans["model_short"] = humans["ai_model"].map(
        lambda model_string: display_model_name(model_string)
    )

    human_means = (
        humans.groupby(["question_id", "ai_model", "human_persona"])["score"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "human_score", "count": "n_humans"})
    )

    ai_scores = ai_responses.rename(
        columns={
            "source_model": "ai_model",
            "persona_name": "ai_persona",
            "score": "ai_score",
        }
    )[["question_id", "ai_model", "ai_persona", "ai_score", "group_name"]]

    bridging = bridging.rename(columns={"response_model": "ai_model"})

    return SurveyFrames(
        humans=humans,
        human_means=human_means,
        ai_scores=ai_scores,
        bridging=bridging,
    )


def model_display_order(humans: pd.DataFrame) -> list[str]:
    """Return human-model display labels in the order defined by ``config``.

    Parameters:
        humans: Frame with an ``ai_model`` column (raw provider:model strings).

    Returns:
        List of display names for every model present in ``humans``, ordered
        to match :data:`config.MODEL_DISPLAY_NAMES` first, then any unknown
        models appended in their original order.
    """
    present_models = list(dict.fromkeys(humans["ai_model"].tolist()))
    known_order = [model for model in config.MODEL_DISPLAY_NAMES if model in present_models]
    unknown = [model for model in present_models if model not in config.MODEL_DISPLAY_NAMES]
    return [display_model_name(model) for model in known_order + unknown]
