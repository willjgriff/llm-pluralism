"""Normalise model text and load response CSV rows."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def normalize_yes_no(value: str) -> str:
    """
    Map free-form model output to Yes/No/Other.
    Examples:
    - "Yes", "Yes." -> "Yes"
    - "No", "No." -> "No"
    """
    normalized = value.strip().lower()
    if normalized.startswith("yes"):
        return "Yes"
    if normalized.startswith("no"):
        return "No"
    return "Other"


def read_responses(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))
