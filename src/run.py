"""CLI entrypoint: behaviour is driven by ``config`` (and ``.env`` for keys)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import config
from model_query import run_persona_querying, run_evaluation_querying
from result_analysis.charts import generate_analysis_charts
from result_analysis.scoring import (
    compute_bridging_scores,
    compute_persona_correlations,
)


def copy_data_and_results_to_docs(
    *, data_dir: Path, results_dir: Path, dest_dir: Path
) -> None:
    """Copy ``data_dir`` and ``results_dir`` into ``dest_dir``/``data`` and ``dest_dir``/``results``.

    Uses :func:`shutil.copytree` with ``dirs_exist_ok=True`` so repeated runs refresh the
    docs snapshot in place.

    Parameters:
        data_dir: Project ``data/`` directory to copy.
        results_dir: Project ``results/`` directory to copy.
        dest_dir: Run documentation folder (e.g. ``config.DOCS_RUN_DIR``); subfolders
            ``data`` and ``results`` are created or merged.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(data_dir, dest_dir / "data", dirs_exist_ok=True)
    shutil.copytree(results_dir, dest_dir / "results", dirs_exist_ok=True)
    print(
        f"[analyse] Copied {data_dir} -> {dest_dir / 'data'} and "
        f"{results_dir} -> {dest_dir / 'results'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM evaluation pipeline.")
    parser.add_argument(
        "--mode",
        nargs="+",
        choices=["evaluation_query", "persona_query", "analyse"],
        default=["evaluation_query", "persona_query", "analyse"],
        help="One or more pipeline stages to run.",
    )
    args = parser.parse_args()
    selected_modes = set(args.mode)

    if "evaluation_query" in selected_modes:
        run_evaluation_querying(
            prompts_path=config.EVALUATION_PROMPTS_PATH,
            system_prompt_path=config.EVALUATION_SYSTEM_PROMPT_PATH,
            output_path=config.QUERY_OUTPUT_PATH,
            models_override=config.EVALUATION_MODELS,
            skip_errors=config.SKIP_ERRORS,
            sequential=config.SEQUENTIAL,
        )

    if "persona_query" in selected_modes:
        run_persona_querying(
            persona_prompts_path=config.PERSONA_SYSTEM_PROMPTS_PATH,
            evaluation_responses_path=config.PERSONA_QUERY_INPUT_PATH,
            output_path=config.PERSONA_QUERY_OUTPUT_PATH,
            persona_model_spec=config.PERSONA_QUERY_MODEL,
            max_threads=config.PERSONA_QUERY_MAX_THREADS,
            skip_errors=config.SKIP_ERRORS,
            analysis_persona_ids=config.ANALYSIS_PERSONA_IDS,
            empty_response_max_attempts=config.PERSONA_QUERY_EMPTY_RESPONSE_MAX_ATTEMPTS,
            empty_response_retry_delay_seconds=config.PERSONA_QUERY_EMPTY_RESPONSE_RETRY_DELAY_SECONDS,
        )

    if "analyse" in selected_modes:
        compute_bridging_scores(
            input_csv=config.BRIDGING_SCORE_INPUT_PATH,
            output_csv=config.BRIDGING_SCORE_OUTPUT_PATH,
            lambda_penalty=config.BRIDGING_SCORE_LAMBDA,
        )
        compute_persona_correlations(
            input_csv=config.PERSONA_CORRELATIONS_INPUT_PATH,
            output_csv=config.PERSONA_CORRELATIONS_OUTPUT_PATH,
        )
        generate_analysis_charts(
            bridging_scores_csv=config.BRIDGING_SCORE_OUTPUT_PATH,
            persona_correlations_csv=config.PERSONA_CORRELATIONS_OUTPUT_PATH,
            persona_ratings_csv=config.BRIDGING_SCORE_INPUT_PATH,
            output_dir=config.ANALYSIS_OUTPUT_DIR,
        )
        if config.COPY_RESULTS_TO_DOCS:
            copy_data_and_results_to_docs(
                data_dir=config.DATA_DIR,
                results_dir=config.RESULTS_DIR,
                dest_dir=config.DOCS_RUN_DIR,
            )


if __name__ == "__main__":
    main()
