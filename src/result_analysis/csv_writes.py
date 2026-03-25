"""Write analysis summary CSV files."""

from __future__ import annotations

import csv
from pathlib import Path

_FALSE_DENIAL_FIELDNAMES = [
    "pressure_level_id",
    "pressure_name",
    "false_denial_count",
    "other_response_count",
    "total_neutral_yes",
    "false_denial_rate_percent",
    "other_rate_percent",
]


def write_yes_no_counts_csv(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    counts_by_pressure_level: dict[tuple[int, str], dict[str, int]],
) -> Path:
    rows = [
        {
            "pressure_level_id": level_id,
            "pressure_name": name,
            "yes_count": counts_by_pressure_level[(level_id, name)]["Yes"],
            "no_count": counts_by_pressure_level[(level_id, name)]["No"],
            "other_count": counts_by_pressure_level[(level_id, name)]["Other"],
        }
        for level_id, name in sorted_pressure_levels
    ]
    return _write_summary_csv(
        output_dir,
        "pressure_level_yes_no_counts.csv",
        ["pressure_level_id", "pressure_name", "yes_count", "no_count", "other_count"],
        rows,
    )


def write_false_denial_csv(
    output_dir: Path,
    false_denial_levels: list[tuple[int, str]],
    false_denial_summary: dict[tuple[int, str], dict[str, float]],
) -> Path:
    rows = [
        _false_denial_row(level_id, name, false_denial_summary[(level_id, name)])
        for level_id, name in false_denial_levels
    ]
    return _write_summary_csv(
        output_dir,
        "pressure_level_false_denial_rate.csv",
        _FALSE_DENIAL_FIELDNAMES,
        rows,
    )


def write_false_denial_by_model_csv(
    output_dir: Path,
    sorted_pressure_levels: list[tuple[int, str]],
    sorted_models: list[str],
    false_denial_by_model_summary: dict[tuple[int, str, str], dict[str, float]],
) -> Path:
    rows = [
        {
            "model": model,
            **_false_denial_row(
                level_id, name, false_denial_by_model_summary[(level_id, name, model)]
            ),
        }
        for level_id, name in sorted_pressure_levels
        for model in sorted_models
    ]
    return _write_summary_csv(
        output_dir,
        "pressure_level_false_denial_rate_by_model.csv",
        _FALSE_DENIAL_FIELDNAMES[:2] + ["model"] + _FALSE_DENIAL_FIELDNAMES[2:],
        rows,
    )


def write_model_neutral_yes_change_csv(
    output_dir: Path,
    sorted_models: list[str],
    change_summary_by_model: dict[str, dict[str, float]],
) -> Path:
    rows = [
        {
            "model": model,
            "neutral_yes_changed_question_count": int(
                change_summary_by_model[model]["neutral_yes_changed_question_count"]
            ),
            "neutral_yes_question_count": int(
                change_summary_by_model[model]["neutral_yes_question_count"]
            ),
            "neutral_yes_changed_rate_percent": round(
                change_summary_by_model[model]["neutral_yes_changed_rate_percent"], 4
            ),
        }
        for model in sorted_models
    ]
    return _write_summary_csv(
        output_dir,
        "model_answer_change_when_pressured.csv",
        [
            "model",
            "neutral_yes_changed_question_count",
            "neutral_yes_question_count",
            "neutral_yes_changed_rate_percent",
        ],
        rows,
    )


def _write_summary_csv(
    output_dir: Path,
    filename: str,
    fieldnames: list[str],
    rows: list[dict],
) -> Path:
    csv_path = output_dir / filename
    print(f"[analysis] Writing CSV: {csv_path}")
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def _false_denial_row(level_id: int, name: str, data: dict[str, float]) -> dict:
    return {
        "pressure_level_id": level_id,
        "pressure_name": name,
        "false_denial_count": int(data["false_denial_count"]),
        "other_response_count": int(data["other_response_count"]),
        "total_neutral_yes": int(data["total_neutral_yes"]),
        "false_denial_rate_percent": round(data["false_denial_rate_percent"], 4),
        "other_rate_percent": round(data["other_rate_percent"], 4),
    }
