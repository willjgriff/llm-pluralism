"""Core query pipeline: evaluation prompts, fixed system prompt, responses CSV."""

from __future__ import annotations

import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from model_query.models import ModelConfig, default_model_configs, generate_answer, parse_model_specs
from prompts import (
    EvaluationPromptRow,
    load_evaluation_prompts,
    load_evaluation_responses,
    load_persona_system_prompts,
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

PERSONA_RESPONSES_CSV_FIELD_NAMES = [
    "question_id",
    "group_id",
    "group_name",
    "source_model",
    "question",
    "source_response",
    "persona_id",
    "persona_name",
    "opposite_persona_id",
    "model",
    "response",
]


def write_evaluation_responses_csv(
    *, output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    _write_rows_csv(
        output_path=output_path,
        rows=rows,
        field_names=RESPONSES_CSV_FIELD_NAMES,
    )


def write_persona_responses_csv(
    *, output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    _write_rows_csv(
        output_path=output_path,
        rows=rows,
        field_names=PERSONA_RESPONSES_CSV_FIELD_NAMES,
    )


def _write_rows_csv(
    *,
    output_path: Path,
    rows: list[dict[str, str | int | float]],
    field_names: list[str],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=field_names)
        writer.writeheader()
        for row_data in rows:
            writer.writerow(
                {
                    field_name: row_data.get(field_name, "")
                    for field_name in field_names
                }
            )


def _try_generate_response(
    *,
    model_config: ModelConfig,
    system_instruction: str,
    question: str,
    skip_errors: bool,
) -> str:
    try:
        return generate_answer(
            instruction=system_instruction,
            question=question,
            config=model_config,
        )
    except Exception as exception_error:
        if not skip_errors:
            raise
        return f"[ERROR] {type(exception_error).__name__}: {str(exception_error)}"


def _query_single_model(
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
        response_text = _try_generate_response(
            model_config=model_config,
            system_instruction=system_instruction,
            question=prompt_row.question,
            skip_errors=skip_errors,
        )
        rows.append(
            {
                "question_id": prompt_row.question_id,
                "group_id": prompt_row.group_id,
                "group_name": prompt_row.group_name,
                "model": model_label,
                "question": prompt_row.question,
                "response": response_text,
            }
        )
    with progress_lock:
        print(
            f"[parallel] Completed model {model_index}/{total_models}: "
            f"{model_label} ({call_index}/{total_per_model} calls)"
        )
    return rows


def run_persona_querying(
    *,
    persona_prompts_path: Path,
    evaluation_responses_path: Path,
    output_path: Path,
    persona_model_spec: str,
    skip_errors: bool,
) -> None:
    persona_rows = load_persona_system_prompts(persona_prompts_path)
    evaluation_rows = load_evaluation_responses(evaluation_responses_path)

    model_spec = persona_model_spec.strip()
    if not model_spec:
        raise ValueError("persona_model_spec must be a non-empty 'provider:model' value.")
    model_configs = parse_model_specs([model_spec])

    total_expected = len(persona_rows) * len(evaluation_rows)
    print(
        "Starting persona query run: "
        f"{len(persona_rows)} personas x {len(evaluation_rows)} evaluation responses "
        f"x 1 model = {total_expected} API calls"
    )

    output_rows: list[dict[str, str | int | float]] = []
    model_config = model_configs[0]
    model_label = f"{model_config.provider}:{model_config.model}"
    print(f"[persona] Using model: {model_label}")
    completed_calls = 0
    for persona_index, persona_row in enumerate(persona_rows, start=1):
        print(
            f"[persona] Starting persona {persona_index}/{len(persona_rows)}: "
            f"{persona_row.persona_id} ({persona_row.persona_name})"
        )
        for evaluation_row in evaluation_rows:
            response_text = _try_generate_response(
                model_config=model_config,
                system_instruction=persona_row.system_prompt,
                question=evaluation_row.source_response,
                skip_errors=skip_errors,
            )
            output_rows.append(
                {
                    "question_id": evaluation_row.question_id,
                    "group_id": evaluation_row.group_id,
                    "group_name": evaluation_row.group_name,
                    "source_model": evaluation_row.source_model,
                    "question": evaluation_row.question,
                    "source_response": evaluation_row.source_response,
                    "persona_id": persona_row.persona_id,
                    "persona_name": persona_row.persona_name,
                    "opposite_persona_id": persona_row.opposite_persona_id,
                    "model": model_label,
                    "response": response_text,
                }
            )
            completed_calls += 1
            if completed_calls % 10 == 0 or completed_calls == total_expected:
                print(f"[persona] Progress: {completed_calls}/{total_expected} calls")

    write_persona_responses_csv(output_path=output_path, rows=output_rows)
    print(f"Wrote {len(output_rows)} rows to {output_path}")


def run_evaluation_querying(
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
    system_prompt = load_system_prompt(system_prompt_path)

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
                _query_single_model(
                    model_config=model_config,
                    prompts=prompts,
                    system_instruction=system_prompt,
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
                        _query_single_model,
                        model_config=model_config,
                        prompts=prompts,
                        system_instruction=system_prompt,
                        skip_errors=skip_errors,
                        model_index=model_index,
                        total_models=len(model_configs),
                        total_per_model=total_per_model,
                        progress_lock=progress_lock,
                    )
                )
            for future in as_completed(submitted_futures):
                output_rows.extend(future.result())

    write_evaluation_responses_csv(output_path=output_path, rows=output_rows)
    print(f"Wrote {len(output_rows)} rows to {output_path}")
