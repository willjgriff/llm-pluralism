"""Prompt loading for evaluation-style runs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationPromptRow:
    question_id: int
    group_id: int
    group_name: str
    question: str


@dataclass(frozen=True)
class PersonaPromptRow:
    persona_id: int
    persona_name: str
    opposite_persona_id: int
    system_prompt: str


@dataclass(frozen=True)
class EvaluationResponseRow:
    question_id: int
    group_id: int
    group_name: str
    source_model: str
    question: str
    source_response: str


def load_evaluation_prompts(csv_path: Path) -> list[EvaluationPromptRow]:
    """
    Load prompts from an evaluation CSV.

    Expected columns:
      - question_id (int)
      - group_id (int)
      - group_name (str)
      - prompt (str)

    We map:
      - question := prompt
    """
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        prompt_rows: list[EvaluationPromptRow] = []
        for row_index, row_data in enumerate(reader, start=1):
            question_id_raw = (row_data.get("question_id") or "").strip()
            group_id_raw = (row_data.get("group_id") or "").strip()
            group_name = (row_data.get("group_name") or "").strip()
            prompt_text = (row_data.get("prompt") or "").strip()

            if not group_id_raw:
                raise ValueError(
                    f"Missing required column value 'group_id' in {csv_path}. "
                    "Expected `group_id` to be an integer."
                )
            if not prompt_text:
                raise ValueError(
                    f"Missing required column value 'prompt' in {csv_path}."
                )
            if not group_name:
                raise ValueError(
                    f"Missing required column value 'group_name' in {csv_path}."
                )

            # If older CSVs don’t include question_id, fall back to row order.
            question_id = int(question_id_raw) if question_id_raw else row_index

            prompt_rows.append(
                EvaluationPromptRow(
                    question_id=question_id,
                    group_id=int(group_id_raw),
                    group_name=group_name,
                    question=prompt_text,
                )
            )
    return prompt_rows


def load_persona_system_prompts(csv_path: Path) -> list[PersonaPromptRow]:
    """
    Load persona system prompts from CSV.

    Expected columns:
      - persona_id (int)
      - persona_name (str)
      - opposite_persona_id (int)
      - system_prompt (str)
    """
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        persona_rows: list[PersonaPromptRow] = []
        for row_data in reader:
            persona_id_raw = (row_data.get("persona_id") or "").strip()
            persona_name = (row_data.get("persona_name") or "").strip()
            opposite_persona_id_raw = (row_data.get("opposite_persona_id") or "").strip()
            system_prompt = (row_data.get("system_prompt") or "").strip()

            if not persona_id_raw:
                raise ValueError(
                    f"Missing required column value 'persona_id' in {csv_path}. "
                    "Expected `persona_id` to be an integer."
                )
            if not persona_name:
                raise ValueError(
                    f"Missing required column value 'persona_name' in {csv_path}."
                )
            if not opposite_persona_id_raw:
                raise ValueError(
                    f"Missing required column value 'opposite_persona_id' in {csv_path}. "
                    "Expected `opposite_persona_id` to be an integer."
                )
            if not system_prompt:
                raise ValueError(
                    f"Missing required column value 'system_prompt' in {csv_path}."
                )

            persona_rows.append(
                PersonaPromptRow(
                    persona_id=int(persona_id_raw),
                    persona_name=persona_name,
                    opposite_persona_id=int(opposite_persona_id_raw),
                    system_prompt=system_prompt,
                )
            )
    return persona_rows


def load_evaluation_responses(csv_path: Path) -> list[EvaluationResponseRow]:
    """
    Load model responses from evaluation responses CSV.

    Expected columns:
      - question_id (int)
      - group_id (int)
      - group_name (str)
      - model (str)
      - question (str)
      - response (str)
    """
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {
            "question_id",
            "group_id",
            "group_name",
            "model",
            "question",
            "response",
        }
        if reader.fieldnames is None:
            raise ValueError(f"{csv_path} has no CSV header row.")
        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns in {csv_path}: {sorted(missing)}")

        rows: list[EvaluationResponseRow] = []
        for row_data in reader:
            question_id_raw = (row_data.get("question_id") or "").strip()
            group_id_raw = (row_data.get("group_id") or "").strip()
            group_name = (row_data.get("group_name") or "").strip()
            source_model = (row_data.get("model") or "").strip()
            question = (row_data.get("question") or "").strip()
            source_response = (row_data.get("response") or "").strip()

            if not question_id_raw:
                raise ValueError(
                    f"Missing required column value 'question_id' in {csv_path}."
                )
            if not group_id_raw:
                raise ValueError(
                    f"Missing required column value 'group_id' in {csv_path}."
                )
            if not group_name:
                raise ValueError(
                    f"Missing required column value 'group_name' in {csv_path}."
                )
            if not source_model:
                raise ValueError(f"Missing required column value 'model' in {csv_path}.")
            if not question:
                raise ValueError(
                    f"Missing required column value 'question' in {csv_path}."
                )
            if not source_response:
                raise ValueError(
                    f"Missing required column value 'response' in {csv_path}."
                )

            rows.append(
                EvaluationResponseRow(
                    question_id=int(question_id_raw),
                    group_id=int(group_id_raw),
                    group_name=group_name,
                    source_model=source_model,
                    question=question,
                    source_response=source_response,
                )
            )
    return rows


def load_system_prompt(txt_path: Path) -> str:
    """Load a shared system prompt from a plain text file."""
    return txt_path.read_text(encoding="utf-8").strip()
