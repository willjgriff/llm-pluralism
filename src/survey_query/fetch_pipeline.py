"""Download the survey export JSON and save sessions and ratings CSVs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


def run_survey_export_fetch(
    *,
    export_url: str,
    export_password: str,
    sessions_csv: Path,
    ratings_csv: Path,
) -> None:
    """Fetch the combined sessions/ratings export and write two CSV files.

    Performs an HTTP GET against ``export_url`` with HTTP Basic auth
    (username ``admin``, password ``export_password``), parses the
    JSON body's ``sessions`` and ``ratings`` arrays, and writes them
    to disk as separate CSVs.

    Parameters:
        export_url: Full URL of the export endpoint
            (e.g. ``https://api.example.org/export/all``).
        export_password: HTTP Basic auth password (typically loaded
            from ``EXPORT_PASSWORD`` in ``.env``).
        sessions_csv: Path to write the sessions CSV to. Parent
            directories are created if needed.
        ratings_csv: Path to write the ratings CSV to. Parent
            directories are created if needed.

    Returns:
        Nothing. Prints one summary line per output file.
    """
    response = requests.get(
        export_url,
        auth=HTTPBasicAuth("admin", export_password),
        timeout=60,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    payload = response.json()

    sessions = payload.get("sessions") or []
    ratings = payload.get("ratings") or []

    sessions_csv.parent.mkdir(parents=True, exist_ok=True)
    ratings_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sessions).to_csv(sessions_csv, index=False)
    pd.DataFrame(ratings).to_csv(ratings_csv, index=False)

    print(f"[survey_query] Wrote {len(sessions)} session row(s) -> {sessions_csv}")
    print(f"[survey_query] Wrote {len(ratings)} rating row(s) -> {ratings_csv}")
