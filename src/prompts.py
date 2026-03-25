"""Prompt loading for axis-style evaluation runs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptRow:
    question_id: int
    axis: int
    axis_name: str
    question: str


def load_evaluation_prompts(csv_path: Path) -> list[PromptRow]:
    """
    Load prompts from an evaluation CSV.

    Expected columns:
      - question_id (int)
      - axis (int)
      - axis_name (str)
      - prompt (str)

    We map:
      - question := prompt
    """
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        prompt_rows: list[PromptRow] = []
        for row_index, row_data in enumerate(reader, start=1):
            question_id_raw = (row_data.get("question_id") or "").strip()
            axis_raw = (row_data.get("axis") or "").strip()
            axis_name = (row_data.get("axis_name") or "").strip()
            prompt_text = (row_data.get("prompt") or "").strip()

            if not axis_raw:
                raise ValueError(
                    f"Missing required column value 'axis' in {csv_path}. "
                    "Expected `axis` to be an integer."
                )
            if not prompt_text:
                raise ValueError(
                    f"Missing required column value 'prompt' in {csv_path}."
                )
            if not axis_name:
                raise ValueError(
                    f"Missing required column value 'axis_name' in {csv_path}."
                )

            # If older CSVs don’t include question_id, fall back to row order.
            question_id = int(question_id_raw) if question_id_raw else row_index

            prompt_rows.append(
                PromptRow(
                    question_id=question_id,
                    axis=int(axis_raw),
                    axis_name=axis_name,
                    question=prompt_text,
                )
            )
    return prompt_rows


def load_system_prompt(txt_path: Path) -> str:
    """Load a shared system prompt from a plain text file."""
    return txt_path.read_text(encoding="utf-8").strip()
