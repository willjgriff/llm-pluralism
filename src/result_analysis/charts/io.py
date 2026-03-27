"""CSV helpers for chart inputs."""

from __future__ import annotations

import csv
from pathlib import Path


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    """Load all rows from a UTF-8 CSV as string dictionaries."""
    with csv_path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))
