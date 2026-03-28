"""Core query pipeline: evaluation prompts, fixed system prompt, responses CSV."""

from __future__ import annotations

import csv
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from model_query.models import ModelConfig, default_model_configs, generate_answer, parse_model_specs
from prompts import (
    EvaluationPromptRow,
    PersonaPromptRow,
    load_evaluation_prompts,
    load_evaluation_responses,
    load_persona_system_prompts,
    load_system_prompt,
)

EVALUATION_RESPONSES_CSV_FIELD_NAMES = [
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
    "score",
    "response",
]


def _persona_rating_score_digit(response_text: str) -> str:
    """Normally the rating is the first non-space character; some outputs prefix markdown
    (e.g. ``**3**``), so we scan left-to-right for the first ``1``..``5`` character."""
    for char in response_text:
        if char in {"1", "2", "3", "4", "5"}:
            return char
    return ""


def write_evaluation_responses_csv(
    *, output_path: Path, rows: list[dict[str, str | int | float]]
) -> None:
    _write_rows_csv(
        output_path=output_path,
        rows=rows,
        field_names=EVALUATION_RESPONSES_CSV_FIELD_NAMES,
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
    max_threads: int,
    skip_errors: bool,
    analysis_persona_ids: tuple[int, ...],
) -> None:
    start_time = time.perf_counter()
    all_persona_rows = load_persona_system_prompts(persona_prompts_path)
    persona_by_id = {row.persona_id: row for row in all_persona_rows}
    persona_rows = [persona_by_id[persona_id] for persona_id in analysis_persona_ids]

    evaluation_rows = load_evaluation_responses(evaluation_responses_path)
    model_configs = parse_model_specs([persona_model_spec.strip()])

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
    print(f"[persona] Running with up to {max_threads} concurrent requests.")
    progress_lock = threading.Lock()
    completed_calls = 0
    tasks: list[tuple] = []
    for persona_row in persona_rows:
        for evaluation_row in evaluation_rows:
            tasks.append((persona_row, evaluation_row))

    def _run_persona_call(persona_row, evaluation_row) -> dict[str, str | int | float]:
        response_text = _try_generate_response(
            model_config=model_config,
            system_instruction=persona_row.system_prompt,
            question=evaluation_row.source_response,
            skip_errors=skip_errors,
        )
        return {
            "question_id": evaluation_row.question_id,
            "group_id": evaluation_row.group_id,
            "group_name": evaluation_row.group_name,
            "source_model": evaluation_row.source_model,
            "question": evaluation_row.question,
            "source_response": evaluation_row.source_response,
            "persona_id": persona_row.persona_id,
            "persona_name": persona_row.persona_name,
            "score": _persona_rating_score_digit(response_text),
            "response": response_text,
        }

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(_run_persona_call, persona_row, evaluation_row)
            for persona_row, evaluation_row in tasks
        ]
        for future in as_completed(futures):
            output_rows.append(future.result())
            with progress_lock:
                completed_calls += 1
                if completed_calls % 25 == 0 or completed_calls == total_expected:
                    print(f"[persona] Progress: {completed_calls}/{total_expected} calls")

    write_persona_responses_csv(output_path=output_path, rows=output_rows)
    elapsed_seconds = time.perf_counter() - start_time
    elapsed_minutes = int(elapsed_seconds // 60)
    elapsed_remainder_seconds = int(elapsed_seconds % 60)
    print(
        f"Wrote {len(output_rows)} rows to {output_path} "
        f"in {elapsed_minutes}m {elapsed_remainder_seconds}s"
    )


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
    start_time = time.perf_counter()
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
            completed_models = 0
            for future in as_completed(submitted_futures):
                output_rows.extend(future.result())
                completed_models += 1
                print(
                    f"[parallel] Progress: completed {completed_models}/{len(model_configs)} model runs"
                )

    write_evaluation_responses_csv(output_path=output_path, rows=output_rows)
    elapsed_seconds = time.perf_counter() - start_time
    elapsed_minutes = int(elapsed_seconds // 60)
    elapsed_remainder_seconds = int(elapsed_seconds % 60)
    print(
        f"Wrote {len(output_rows)} rows to {output_path} "
        f"in {elapsed_minutes}m {elapsed_remainder_seconds}s"
    )
