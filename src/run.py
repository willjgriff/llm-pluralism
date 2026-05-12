"""CLI entrypoint: behaviour is driven by ``config`` (and ``.env`` for keys)."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import config
from model_query import run_persona_querying, run_evaluation_querying
from result_analysis.human_survey import generate_survey_analysis
from result_analysis.model_personas import generate_model_persona_analysis
from survey_query import run_survey_export_fetch


def copy_data_and_output_to_docs(
    *, data_dir: Path, output_dir: Path, dest_dir: Path
) -> None:
    """Copy ``data_dir`` and ``output_dir`` into ``dest_dir``/``data`` and ``dest_dir``/``output``.

    Uses :func:`shutil.copytree` with ``dirs_exist_ok=True`` so repeated runs refresh the
    docs snapshot in place.

    Parameters:
        data_dir: Project ``data/`` directory to copy.
        output_dir: Project ``output/`` directory to copy.
        dest_dir: Run documentation folder (e.g. ``config.DOCS_RUN_DIR``); subfolders
            ``data`` and ``output`` are created or merged.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(data_dir, dest_dir / "data", dirs_exist_ok=True)
    shutil.copytree(output_dir, dest_dir / "output", dirs_exist_ok=True)
    print(
        f"[docs] Copied {data_dir} -> {dest_dir / 'data'} and "
        f"{output_dir} -> {dest_dir / 'output'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM evaluation pipeline.")
    parser.add_argument(
        "--mode",
        nargs="+",
        choices=[
            "evaluation_query",
            "persona_query",
            "survey_query",
            "persona_response_analyse",
            "survey_response_analyse",
        ],
        default=[
            "evaluation_query",
            "persona_query",
            "survey_query",
            "persona_response_analyse",
            "survey_response_analyse",
        ],
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

    if "survey_query" in selected_modes:
        run_survey_export_fetch(
            export_url=config.SURVEY_EXPORT_URL,
            export_password=config.EXPORT_PASSWORD,
            sessions_csv=config.SURVEY_SESSIONS_PATH,
            ratings_csv=config.SURVEY_RATINGS_PATH,
        )

    if "persona_response_analyse" in selected_modes:
        generate_model_persona_analysis(
            persona_responses_csv=config.PERSONA_QUERY_OUTPUT_PATH,
            bridging_scores_csv=config.BRIDGING_SCORE_OUTPUT_PATH,
            persona_correlations_csv=config.PERSONA_CORRELATIONS_OUTPUT_PATH,
            bridging_score_lambda=config.BRIDGING_SCORE_LAMBDA,
            output_dir=config.ANALYSIS_OUTPUT_DIR,
        )

    if "survey_response_analyse" in selected_modes:
        generate_survey_analysis(
            sessions_csv=config.SURVEY_SESSIONS_PATH,
            ratings_csv=config.SURVEY_RATINGS_PATH,
            persona_responses_csv=config.PERSONA_QUERY_OUTPUT_PATH,
            bridging_scores_csv=config.BRIDGING_SCORE_OUTPUT_PATH,
            output_dir=config.SURVEY_ANALYSIS_OUTPUT_DIR,
        )

    analysis_modes_selected = selected_modes & {
        "persona_response_analyse",
        "survey_response_analyse",
    }
    if config.COPY_RESULTS_TO_DOCS and analysis_modes_selected:
        copy_data_and_output_to_docs(
            data_dir=config.DATA_DIR,
            output_dir=config.OUTPUT_DIR,
            dest_dir=config.DOCS_RUN_DIR,
        )


if __name__ == "__main__":
    main()
