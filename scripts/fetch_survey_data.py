"""Download combined sessions and ratings JSON from the Railway export API and save two CSVs.

HTTP Basic auth: user ``admin``, password from :data:`config.EXPORT_PASSWORD` (``EXPORT_PASSWORD`` in ``.env``).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


def _import_config_module():
    """Import project config so ``EXPORT_PASSWORD`` loads from ``.env`` when run from repo root."""
    try:
        import config  # type: ignore

        return config
    except ModuleNotFoundError:
        repository_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repository_root / "src"))
        import config  # type: ignore

        return config


config = _import_config_module()

EXPORT_ALL_URL = (
    "https://sparkling-vitality-production-370c.up.railway.app/export/all"
)
SESSIONS_CSV_PATH = Path("output/scripts/railway_export_sessions.csv")
RATINGS_CSV_PATH = Path("output/scripts/railway_export_ratings.csv")


def _fetch_export_payload(url: str) -> dict:
    """GET JSON from ``url`` with HTTP Basic auth (admin / ``config.EXPORT_PASSWORD``).

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
    requests.RequestException
        On network failure or non-success HTTP status.
    ValueError
        If the response body is not a JSON object.
    """
    response = requests.get(
        url,
        auth=HTTPBasicAuth("admin", config.EXPORT_PASSWORD),
        timeout=60,
        headers={"Accept": "application/json"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Export endpoint did not return a JSON object.")
    return payload


def main() -> None:
    """Fetch export JSON and write sessions and ratings to separate CSV files."""
    try:
        payload = _fetch_export_payload(EXPORT_ALL_URL)
    except requests.RequestException as request_error:
        print(f"Request failed: {request_error}", file=sys.stderr)
        raise SystemExit(1) from request_error
    except ValueError as value_error:
        print(f"Invalid response: {value_error}", file=sys.stderr)
        raise SystemExit(1) from value_error

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
