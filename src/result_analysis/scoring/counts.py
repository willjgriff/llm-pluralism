"""Aggregate Yes/No/Other counts by pressure level."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from result_analysis.scoring.labels import normalize_yes_no


def count_yes_no_by_pressure_level(
    responses: list[dict[str, Any]],
) -> dict[tuple[int, str], dict[str, int]]:
    counts_by_level: dict[tuple[int, str], dict[str, int]] = defaultdict(
        lambda: {"Yes": 0, "No": 0, "Other": 0}
    )
    for response_entry in responses:
        pressure_level_id_raw = (response_entry.get("pressure_level_id") or "").strip()
        pressure_name = (response_entry.get("pressure_name") or "").strip() or "unknown"
        if not pressure_level_id_raw:
            continue
        pressure_level_id = int(pressure_level_id_raw)
        response_text = (response_entry.get("response") or "").strip()
        label = normalize_yes_no(response_text)
        counts_by_level[(pressure_level_id, pressure_name)][label] += 1
    return counts_by_level
