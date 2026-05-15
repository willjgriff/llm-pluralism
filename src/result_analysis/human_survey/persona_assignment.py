"""Assign human persona groups for survey analysis (including society-axis reassignment)."""

from __future__ import annotations

import pandas as pd

from result_analysis.human_survey.constants import CENTRIST_THRESHOLD

_AXIS_SCORE_COLUMNS = {
    "economic": "economic_score",
    "identity": "identity_score",
    "technology": "technology_score",
}
_AXIS_PERSONA_COLUMNS = {
    "economic": "economic_persona",
    "identity": "identity_persona",
    "technology": "technology_persona",
}
_NON_SOCIETY_AXES = ("economic", "identity", "technology")


def second_strongest_non_society_persona(session_row: pd.Series) -> str:
    """Return the persona for the strongest non-society axis, or ``Centrist``.

    Parameters:
        session_row: One sessions CSV row with axis score and persona columns.

    Returns:
        Persona name from the winning non-society axis, or ``Centrist`` when the
        strongest absolute score is below :data:`CENTRIST_THRESHOLD`.
    """
    axis_scores = {
        axis_name: abs(session_row[_AXIS_SCORE_COLUMNS[axis_name]])
        for axis_name in _NON_SOCIETY_AXES
    }
    strongest_axis = max(axis_scores, key=axis_scores.__getitem__)
    if axis_scores[strongest_axis] < CENTRIST_THRESHOLD:
        return "Centrist"
    return session_row[_AXIS_PERSONA_COLUMNS[strongest_axis]]


def assign_analysis_persona(session_row: pd.Series) -> str:
    """Assign the persona used for group-level survey analysis.

    Society-primary participants (Religious or Secularist on the questionnaire)
    are reassigned to their second-strongest non-society axis, because the
    Religious/Secularist AI persona pair was excluded from the evaluation panel.

    Parameters:
        session_row: One sessions CSV row with ``primary_axis`` and
            ``primary_persona``.

    Returns:
        Persona name for grouping ratings in charts and correlation matrices.
    """
    if session_row["primary_axis"] == "society":
        return second_strongest_non_society_persona(session_row)
    return session_row["primary_persona"]
