"""Analysis and chart generation for human survey ratings (web export)."""

from __future__ import annotations

from pathlib import Path


def generate_survey_analysis(
    *,
    sessions_csv: Path,
    ratings_csv: Path,
    evaluation_prompts_csv: Path,
    output_dir: Path,
) -> None:
    """Run all survey-data analysis and write resulting charts/CSVs to ``output_dir``.

    Reads human ratings collected via the web survey, joins them to session
    persona metadata and the originating evaluation prompts, and writes the
    aggregated artefacts (charts, summary CSVs) into ``output_dir``.

    Parameters:
        sessions_csv: Path to ``web_export_sessions.csv`` (one row per session,
            includes ``primary_persona`` and ``primary_axis``).
        ratings_csv: Path to ``web_export_ratings.csv`` (one row per rating,
            keyed by ``session_id``, ``question_id``, ``model``).
        evaluation_prompts_csv: Path to the evaluation prompts CSV used to look
            up question text and topic/group for each ``question_id``.
        output_dir: Directory to write generated charts and summary CSVs into;
            created if it does not exist.

    Returns:
        None.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # TODO: implement scoring, joins, and chart generation for survey data.
    print(f"[survey_analyse] Placeholder: would write survey charts to {output_dir}")
