#!/usr/bin/env python3
"""Mean time to complete the first six survey ratings per session (by created_at)."""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RATINGS_CSV = _REPO_ROOT / "output/survey_responses_ratings.csv"
DEFAULT_SESSIONS_CSV = _REPO_ROOT / "output/survey_responses_sessions.csv"
FIRST_RATING_COUNT = 6
SECONDS_PER_MINUTE = 60.0


def load_session_start_times(sessions_path: Path) -> pd.Series:
    """Load session ``created_at`` indexed by session ``id``.

    Parameters:
        sessions_path: Path to ``survey_responses_sessions.csv``.

    Returns:
        Series mapping session id to session start ``created_at`` (timezone-naive).
    """
    sessions = pd.read_csv(sessions_path)
    sessions["created_at"] = pd.to_datetime(
        sessions["created_at"], errors="coerce", utc=False
    )
    return sessions.set_index("id")["created_at"]


def sixth_rating_time(session_ratings: pd.DataFrame, rating_count: int) -> pd.Timestamp:
    """Return ``created_at`` of the Nth earliest rating for a session.

    Parameters:
        session_ratings: Rows for one ``session_id`` with a ``created_at`` column.
        rating_count: Which earliest rating to take (e.g. 6 for the sixth).

    Returns:
        Timestamp of that rating's ``created_at``.
    """
    ordered = session_ratings.sort_values("created_at", kind="mergesort")
    return ordered["created_at"].iloc[rating_count - 1]


def span_seconds_from_session_start(
    session_start: pd.Timestamp, session_ratings: pd.DataFrame, rating_count: int
) -> float:
    """Wall-clock seconds from session start to the Nth rating by ``created_at``.

    Parameters:
        session_start: ``created_at`` from the matching sessions CSV row.
        session_ratings: Rows for one ``session_id`` with a ``created_at`` column.
        rating_count: How many earliest ratings to consider (end point is this rating).

    Returns:
        Elapsed seconds from ``session_start`` to the Nth rating timestamp.
    """
    end_time = sixth_rating_time(session_ratings, rating_count)
    return (end_time - session_start).total_seconds()


def collect_first_six_durations_minutes(
    ratings_path: Path, sessions_path: Path
) -> tuple[list[float], int, int]:
    """Compute per-session duration (minutes) from session start to sixth rating.

    Sessions with fewer than six ratings, or with no sessions row / start time,
    are skipped.

    Parameters:
        ratings_path: Path to ``survey_responses_ratings.csv``.
        sessions_path: Path to ``survey_responses_sessions.csv``.

    Returns:
        Tuple of (durations in minutes for included sessions, skipped for <6 ratings,
        skipped for missing session or session timestamp).
    """
    ratings = pd.read_csv(ratings_path)
    ratings["created_at"] = pd.to_datetime(
        ratings["created_at"], errors="coerce", utc=False
    )
    invalid_rating_timestamps = int(ratings["created_at"].isna().sum())
    if invalid_rating_timestamps:
        print(
            f"Warning: dropped {invalid_rating_timestamps} rating(s) "
            "with unparseable created_at"
        )
        ratings = ratings.dropna(subset=["created_at"])

    session_starts = load_session_start_times(sessions_path)
    invalid_session_starts = int(session_starts.isna().sum())
    if invalid_session_starts:
        print(
            f"Warning: {invalid_session_starts} session(s) have unparseable created_at "
            "and will be skipped if referenced"
        )

    durations_minutes: list[float] = []
    skipped_fewer_than_six = 0
    skipped_no_session = 0

    for session_id, session_frame in ratings.groupby("session_id", sort=False):
        if len(session_frame) < FIRST_RATING_COUNT:
            skipped_fewer_than_six += 1
            continue
        if session_id not in session_starts.index:
            skipped_no_session += 1
            continue
        session_start = session_starts.loc[session_id]
        if pd.isna(session_start):
            skipped_no_session += 1
            continue
        span_seconds = span_seconds_from_session_start(
            session_start, session_frame, FIRST_RATING_COUNT
        )
        durations_minutes.append(span_seconds / SECONDS_PER_MINUTE)

    return durations_minutes, skipped_fewer_than_six, skipped_no_session


def print_duration_summary(
    durations_minutes: list[float],
    *,
    skipped_fewer_than_six: int,
    skipped_no_session: int,
) -> None:
    """Print count of included sessions and mean/median/min/max duration in minutes.

    Parameters:
        durations_minutes: Per-session durations for sessions with at least six ratings.
        skipped_fewer_than_six: Sessions omitted for having fewer than six ratings.
        skipped_no_session: Sessions omitted for missing session row or start time.

    Returns:
        Nothing; writes to stdout.
    """
    included_count = len(durations_minutes)
    print(f"Sessions with < {FIRST_RATING_COUNT} ratings (skipped): {skipped_fewer_than_six}")
    print(f"Sessions missing session row or start time (skipped): {skipped_no_session}")
    print(f"Sessions included: {included_count}")
    if not durations_minutes:
        print("No sessions with enough ratings to compute durations.")
        return

    mean_minutes = statistics.mean(durations_minutes)
    median_minutes = statistics.median(durations_minutes)
    min_minutes = min(durations_minutes)
    max_minutes = max(durations_minutes)

    print()
    print(
        f"Time for first {FIRST_RATING_COUNT} ratings "
        f"(session created_at → {FIRST_RATING_COUNT}th rating created_at):"
    )
    print(f"  Mean:   {mean_minutes:.2f} min")
    print(f"  Median: {median_minutes:.2f} min")
    print(f"  Min:    {min_minutes:.2f} min")
    print(f"  Max:    {max_minutes:.2f} min")


def main() -> None:
    """Parse CLI, load CSVs, and print duration summary for first six ratings."""
    parser = argparse.ArgumentParser(
        description=(
            "For each session with at least six ratings, measure wall-clock time "
            "from the session's created_at to the sixth rating (by rating created_at), "
            "then report mean, median, min, and max in minutes."
        ),
    )
    parser.add_argument(
        "--ratings-csv",
        type=Path,
        default=DEFAULT_RATINGS_CSV,
        help=f"Path to survey ratings export (default: {DEFAULT_RATINGS_CSV})",
    )
    parser.add_argument(
        "--sessions-csv",
        type=Path,
        default=DEFAULT_SESSIONS_CSV,
        help=f"Path to survey sessions export (default: {DEFAULT_SESSIONS_CSV})",
    )
    arguments = parser.parse_args()
    ratings_path = arguments.ratings_csv
    sessions_path = arguments.sessions_csv

    if not ratings_path.is_file():
        raise SystemExit(f"Ratings file not found: {ratings_path}")
    if not sessions_path.is_file():
        raise SystemExit(f"Sessions file not found: {sessions_path}")

    durations_minutes, skipped_few, skipped_no_session = (
        collect_first_six_durations_minutes(ratings_path, sessions_path)
    )
    print(f"Ratings file:  {ratings_path}")
    print(f"Sessions file: {sessions_path}")
    print_duration_summary(
        durations_minutes,
        skipped_fewer_than_six=skipped_few,
        skipped_no_session=skipped_no_session,
    )


if __name__ == "__main__":
    main()
