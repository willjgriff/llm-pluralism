"""Group responses by pressure level and extract comparison keys."""

from __future__ import annotations

from typing import Any

from result_analysis.scoring.labels import normalize_yes_no


def extract_response_key(response_entry: dict[str, Any]) -> tuple[str, str, str]:
    return (
        (response_entry.get("question_id") or "").strip(),
        (response_entry.get("organisation") or "").strip(),
        (response_entry.get("model") or "").strip(),
    )


def split_responses_by_pressure_level(
    responses: list[dict[str, Any]],
) -> tuple[
    dict[tuple[str, str, str], str],
    list[tuple[tuple[str, str, str], int, str, str]],
    set[tuple[int, str]],
]:
    neutral_response_label_by_key: dict[tuple[str, str, str], str] = {}
    non_neutral_response_records: list[tuple[tuple[str, str, str], int, str, str]] = []
    observed_pressure_levels: set[tuple[int, str]] = set()

    for response_entry in responses:
        pressure_level_id_raw = (response_entry.get("pressure_level_id") or "").strip()
        pressure_name = (response_entry.get("pressure_name") or "").strip() or "unknown"
        if not pressure_level_id_raw:
            continue

        pressure_level_id = int(pressure_level_id_raw)
        observed_pressure_levels.add((pressure_level_id, pressure_name))
        response_label = normalize_yes_no((response_entry.get("response") or "").strip())
        response_key = extract_response_key(response_entry)

        if pressure_level_id == 0:
            neutral_response_label_by_key[response_key] = response_label
        else:
            non_neutral_response_records.append(
                (response_key, pressure_level_id, pressure_name, response_label)
            )

    return (
        neutral_response_label_by_key,
        non_neutral_response_records,
        observed_pressure_levels,
    )
