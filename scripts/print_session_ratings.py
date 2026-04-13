#!/usr/bin/env python3
"""Print web-export ratings for a session, joined to prompts, session persona, and evaluation responses."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

# Paths are relative to the repository root (parent of this file's directory).
_REPO_ROOT = Path(__file__).resolve().parent.parent
RATINGS_CSV = _REPO_ROOT / "output/scripts/web_export_ratings.csv"
PROMPTS_CSV = _REPO_ROOT / "data/evaluation_prompts.csv"
SESSIONS_CSV = _REPO_ROOT / "output/scripts/web_export_sessions.csv"
EVALUATION_RESPONSES_CSV = _REPO_ROOT / "output/evaluation_responses.csv"


def _parse_created_at_for_sort(raw_value: str | None) -> datetime:
    """
    Parse created_at from a rating row for chronological sorting.

    Parameters:
        raw_value: Timestamp string from CSV, or None when missing.

    Returns:
        Parsed datetime in local naive form, or datetime.min when empty or invalid.
    """
    text = (raw_value or "").strip()
    if not text:
        return datetime.min
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.min


def load_prompts_by_question_id(prompts_path: Path) -> dict[int, dict[str, str]]:
    """
    Load evaluation prompts keyed by question_id.

    Parameters:
        prompts_path: CSV file with columns including question_id and prompt.

    Returns:
        Mapping from question_id integer to the full row as string-keyed dict.
    """
    by_id: dict[int, dict[str, str]] = {}
    with prompts_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            question_id = int(row["question_id"])
            by_id[question_id] = row
    return by_id


def load_session_by_id(sessions_path: Path, session_id: str) -> dict[str, str] | None:
    """
    Find the session row whose id matches the given session_id.

    Parameters:
        sessions_path: CSV export of sessions (id column matches ratings session_id).
        session_id: UUID string for the session.

    Returns:
        The matching row as a dict, or None if no row exists.
    """
    with sessions_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["id"] == session_id:
                return row
    return None


def load_evaluation_responses_by_key(responses_path: Path) -> dict[tuple[int, str], str]:
    """
    Index evaluation_responses rows by question and model.

    Parameters:
        responses_path: CSV with question_id, model, and response columns.

    Returns:
        Mapping (question_id, model) to the baseline model response text.
        When duplicate keys exist, the first row wins.
    """
    by_key: dict[tuple[int, str], str] = {}
    with responses_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            question_id = int(row["question_id"])
            model_name = (row.get("model") or "").strip()
            key = (question_id, model_name)
            if key in by_key:
                continue
            by_key[key] = row.get("response") or ""
    return by_key


def iter_ratings_for_session(ratings_path: Path, session_id: str) -> list[dict[str, str]]:
    """
    Collect all rating rows for the given session_id.

    Parameters:
        ratings_path: CSV file of web export ratings.
        session_id: UUID string for the session.

    Returns:
        List of rating row dicts (may be empty), sorted by created_at ascending
        (earliest rating first).
    """
    rows: list[dict[str, str]] = []
    with ratings_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["session_id"] == session_id:
                rows.append(row)
    rows.sort(key=lambda rating_row: _parse_created_at_for_sort(rating_row.get("created_at")))
    return rows


def format_rating_block(
    index: int,
    total: int,
    rating_row: dict[str, str],
    prompt_row: dict[str, str] | None,
    evaluation_response_text: str,
) -> str:
    """
    Format one rating for console output.

    Parameters:
        index: One-based index among ratings for this session.
        total: Total number of ratings for this session.
        rating_row: Row from web_export_ratings.csv.
        prompt_row: Matching evaluation_prompts row, or None if question_id is missing.
        evaluation_response_text: Baseline model answer from evaluation_responses.csv
            for this question_id and model, or a placeholder if the row was missing.

    Returns:
        Multi-line string block suitable for printing.
    """
    question_id = int(rating_row["question_id"])
    if prompt_row is None:
        prompt_text = f"(no prompt found for question_id={question_id})"
        group_line = ""
    else:
        prompt_text = prompt_row["prompt"]
        group_name = prompt_row.get("group_name", "").strip()
        group_id = prompt_row.get("group_id", "").strip()
        group_line = f"Topic: {group_name} (group_id={group_id})" if group_name or group_id else ""

    stripped_evaluation = evaluation_response_text.strip()
    evaluation_block = stripped_evaluation if stripped_evaluation else "(empty)"

    reasoning = (rating_row.get("reasoning") or "").strip()
    if not reasoning:
        reasoning = "(none)"

    lines = [
        "=" * 72,
        f"[{index} / {total}]  question_id={question_id}",
        "-" * 72,
    ]
    if group_line:
        lines.append(group_line)
        lines.append("")
    lines.extend(
        [
            "Question:",
            prompt_text,
            "",
            f"Score:      {rating_row.get('score', '')}",
            f"Model:      {rating_row.get('model', '')}",
            f"Created at: {rating_row.get('created_at', '')}",
            "",
            "Evaluation response:",
            evaluation_block,
            "",
            "Reasoning:",
            reasoning,
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    """Parse CLI and print session persona plus formatted ratings for the session."""
    parser = argparse.ArgumentParser(
        description="Print primary persona and all rated questions for a web export session.",
    )
    parser.add_argument(
        "session_id",
        help="Session UUID (matches session_id in ratings and id in sessions export).",
    )
    arguments = parser.parse_args()
    session_id = arguments.session_id

    session_row = load_session_by_id(SESSIONS_CSV, session_id)
    if session_row is None:
        print(f"Warning: no session row in {SESSIONS_CSV} for id={session_id}")
    else:
        primary_persona_display = (session_row.get("primary_persona") or "").strip() or "(unknown)"
        primary_axis = (session_row.get("primary_axis") or "").strip()
        axis_suffix = f" (primary axis: {primary_axis})" if primary_axis else ""
        print(f"Primary persona: {primary_persona_display}{axis_suffix}")
        print()

    evaluation_responses_by_key = load_evaluation_responses_by_key(EVALUATION_RESPONSES_CSV)
    prompts_by_id = load_prompts_by_question_id(PROMPTS_CSV)
    rating_rows = iter_ratings_for_session(RATINGS_CSV, session_id)

    if not rating_rows:
        print(f"No ratings found for session_id={session_id}")
        return

    print(f"Session: {session_id}")
    print(f"Ratings: {len(rating_rows)}")
    print()

    total = len(rating_rows)
    for offset, rating_row in enumerate(rating_rows, start=1):
        question_id = int(rating_row["question_id"])
        prompt_row = prompts_by_id.get(question_id)
        model_name = (rating_row.get("model") or "").strip()
        lookup_key = (question_id, model_name)
        evaluation_response = evaluation_responses_by_key.get(lookup_key)
        if evaluation_response is None:
            evaluation_response = (
                f"(not found in {EVALUATION_RESPONSES_CSV} for question_id={question_id}, "
                f"model={model_name!r})"
            )
        print(format_rating_block(offset, total, rating_row, prompt_row, evaluation_response))


if __name__ == "__main__":
    main()
