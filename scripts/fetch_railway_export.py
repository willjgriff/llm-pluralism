"""Download combined sessions and ratings JSON from the Railway export API and save two CSVs."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

EXPORT_ALL_URL = (
    "https://sparkling-vitality-production-370c.up.railway.app/export/all"
)
SESSIONS_CSV_PATH = Path("output/scripts/railway_export_sessions.csv")
RATINGS_CSV_PATH = Path("output/scripts/railway_export_ratings.csv")


def _fetch_export_payload(url: str) -> dict:
    """GET JSON from ``url`` and parse it as a dict.

    Parameters
    ----------
    url:
        Full URL of the export endpoint.

    Returns
    -------
    dict
        Parsed JSON object (expected keys ``sessions`` and ``ratings``).

    Raises
    ------
    urllib.error.URLError
        On network or HTTP failure.
    ValueError
        If the response is not a JSON object.
    """
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
    payload = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Export endpoint did not return a JSON object.")
    return payload


def main() -> None:
    """Fetch export JSON and write sessions and ratings to separate CSV files."""
    try:
        payload = _fetch_export_payload(EXPORT_ALL_URL)
    except urllib.error.URLError as url_error:
        print(f"Request failed: {url_error}", file=sys.stderr)
        raise SystemExit(1) from url_error
    except (json.JSONDecodeError, ValueError) as parse_error:
        print(f"Invalid response: {parse_error}", file=sys.stderr)
        raise SystemExit(1) from parse_error

    sessions = payload.get("sessions") or []
    ratings = payload.get("ratings") or []
    if not isinstance(sessions, list) or not isinstance(ratings, list):
        print("Expected 'sessions' and 'ratings' to be lists.", file=sys.stderr)
        raise SystemExit(1)

    SESSIONS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sessions).to_csv(SESSIONS_CSV_PATH, index=False)
    pd.DataFrame(ratings).to_csv(RATINGS_CSV_PATH, index=False)

    print(f"Wrote {len(sessions)} session row(s) -> {SESSIONS_CSV_PATH}")
    print(f"Wrote {len(ratings)} rating row(s) -> {RATINGS_CSV_PATH}")


if __name__ == "__main__":
    main()
