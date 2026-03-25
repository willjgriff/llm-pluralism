"""Prompt and pressure-level loading."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ORG_NAME_PLACEHOLDER = "{ORG_NAME}"


@dataclass(frozen=True)
class PromptRow:
    question_id: int
    organisation: str
    question: str
    ground_truth: str


@dataclass(frozen=True)
class PressureLevel:
    """One row from data/pressure_levels.csv; column 'prompt' may contain {ORG_NAME}."""

    pressure_level_id: int
    name: str
    system_instruction_template: str


def load_prompts(csv_path: Path) -> list[PromptRow]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        prompt_rows: list[PromptRow] = []
        for row_data in reader:
            prompt_rows.append(
                PromptRow(
                    question_id=int(row_data["question_id"]),
                    organisation=(row_data.get("organisation") or "").strip(),
                    question=(row_data.get("question") or "").strip(),
                    ground_truth=(row_data.get("ground_truth") or "").strip(),
                )
            )
    return prompt_rows


def load_pressure_levels(csv_path: Path) -> list[PressureLevel]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        levels: list[PressureLevel] = []
        for row_data in reader:
            levels.append(
                PressureLevel(
                    pressure_level_id=int(row_data["pressure_level_id"]),
                    name=(row_data.get("name") or "").strip(),
                    system_instruction_template=(row_data.get("prompt") or "").strip(),
                )
            )
    levels.sort(key=lambda level: level.pressure_level_id)
    return levels


def resolve_system_instruction(
    pressure_level: PressureLevel, organisation: str
) -> str:
    """Substitute organisation name into the pressure-level system prompt."""
    return pressure_level.system_instruction_template.replace(
        ORG_NAME_PLACEHOLDER, organisation
    )


def iter_prompt_pressure_pairs(
    prompts: Iterable[PromptRow], pressure_levels: Iterable[PressureLevel]
) -> Iterable[tuple[PromptRow, PressureLevel]]:
    for prompt_row in prompts:
        for pressure_level in pressure_levels:
            yield prompt_row, pressure_level
