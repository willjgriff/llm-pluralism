"""CLI entrypoint: behaviour is driven by ``config`` (and ``.env`` for keys)."""

from __future__ import annotations

import argparse

import config
from model_query import run_persona_querying, run_evaluation_querying


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
        )

    if "analyse" in selected_modes:
        pass


if __name__ == "__main__":
    main()
