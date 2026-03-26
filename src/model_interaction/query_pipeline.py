"""Core query pipeline: evaluation prompts, fixed system prompt, responses CSV."""

from __future__ import annotations

import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from model_interaction.models import ModelConfig, default_model_configs, generate_answer, parse_model_specs
from prompts import (
    EvaluationPromptRow,
    load_evaluation_prompts,
    load_system_prompt,
)

RESPONSES_CSV_FIELD_NAMES = [
    "question_id",
    "group_id",
    "group_name",
    "model",
    "question",
    "response",
]

def write_responses_csv(
    *, output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=RESPONSES_CSV_FIELD_NAMES)
        writer.writeheader()
        for row_data in rows:
            writer.writerow(
                {
                    field_name: row_data.get(field_name, "")
                    for field_name in RESPONSES_CSV_FIELD_NAMES
                }
            )


def query_single_model(
    *,
    model_config: ModelConfig,
    prompts: list[EvaluationPromptRow],
    system_instruction: str,
    skip_errors: bool,
    model_index: int,
    total_models: int,
    total_per_model: int,  # number of prompt rows for this model
    progress_lock: threading.Lock,
) -> list[dict[str, str | int | float]]:
    """Run all prompt rows for one model (worker-thread safe)."""
    model_label = f"{model_config.provider}:{model_config.model}"
    rows: list[dict[str, str | int | float]] = []
    with progress_lock:
        print(f"[parallel] Started model {model_index}/{total_models}: {model_label}")
    call_index = 0
    for prompt_row in prompts:
        call_index += 1
        with progress_lock:
            print(
                f"[parallel] {model_label} "
                f"({call_index}/{total_per_model}) "
                f"question_id={prompt_row.question_id} "
                f"group={prompt_row.group_id}:{prompt_row.group_name!r} "
            )
        rows.append(
            query_single_prompt(
                model_config=model_config,
                prompt_row=prompt_row,
                system_instruction=system_instruction,
                skip_errors=skip_errors,
            )
        )
    with progress_lock:
        print(
            f"[parallel] Completed model {model_index}/{total_models}: "
            f"{model_label} ({call_index}/{total_per_model} calls)"
        )
    return rows


def query_single_prompt(
    *,
    model_config: ModelConfig,
    prompt_row: EvaluationPromptRow,
    system_instruction: str,
    skip_errors: bool,
) -> dict[str, str | int | float]:
    """
    Query one prompt row with one system prompt using one model.

    This is the primitive operation that can later be reused for workflows where
    each prompt is paired with a different system prompt.
    """
    model_label = f"{model_config.provider}:{model_config.model}"
    try:
        response_text = generate_answer(
            instruction=system_instruction,
            question=prompt_row.question,
            config=model_config,
        )
    except Exception as exception_error:
        if not skip_errors:
            raise
        response_text = (
            f"[ERROR] {type(exception_error).__name__}: {str(exception_error)}"
        )

    return {
        "question_id": prompt_row.question_id,
        "group_id": prompt_row.group_id,
        "group_name": prompt_row.group_name,
        "model": model_label,
        "question": prompt_row.question,
        "response": response_text,
    }


def run_querying(
    *,
    prompts_path: Path,
    system_prompt_path: Path,
    output_path: Path,
    models_override: str,
    skip_errors: bool,
    sequential: bool,
) -> None:
    """
    Load evaluation prompts and a shared system prompt, query all configured models, write CSV.
    """
    prompts = load_evaluation_prompts(prompts_path)

    system_instruction = load_system_prompt(system_prompt_path)
    model_configs = default_model_configs()
    if models_override.strip():
        model_configs = parse_model_specs(models_override.split(","))

    total_per_model = len(prompts)
    total_expected = total_per_model * len(model_configs)
    print(
        "Starting query run: "
        f"{len(prompts)} prompts x {len(model_configs)} models = {total_expected} API calls"
    )
    if sequential:
        print("Mode: sequential (one model at a time).")
    else:
        print(
            f"Mode: parallel — up to {len(model_configs)} models calling APIs at the same time."
        )

    output_rows: list[dict[str, str | int | float]] = []
    progress_lock = threading.Lock()

    if sequential:
        for model_index, model_config in enumerate(model_configs, start=1):
            output_rows.extend(
                query_single_model(
                    model_config=model_config,
                    prompts=prompts,
                    system_instruction=system_instruction,
                    skip_errors=skip_errors,
                    model_index=model_index,
                    total_models=len(model_configs),
                    total_per_model=total_per_model,
                    progress_lock=progress_lock,
                )
            )
    else:
        submitted_futures = []
        with ThreadPoolExecutor(max_workers=len(model_configs)) as executor:
            for model_index, model_config in enumerate(model_configs, start=1):
                submitted_futures.append(
                    executor.submit(
                        query_single_model,
                        model_config=model_config,
                        prompts=prompts,
                        system_instruction=system_instruction,
                        skip_errors=skip_errors,
                        model_index=model_index,
                        total_models=len(model_configs),
                        total_per_model=total_per_model,
                        progress_lock=progress_lock,
                    )
                )
            for future in as_completed(submitted_futures):
                output_rows.extend(future.result())

    write_responses_csv(output_path=output_path, rows=output_rows)
    print(f"Wrote {len(output_rows)} rows to {output_path}")
