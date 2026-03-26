"""CLI entrypoint: behaviour is driven by ``config`` (and ``.env`` for keys)."""

from __future__ import annotations

import argparse

import config
from model_interaction import run_querying
from result_analysis import run_yes_no_analysis


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM evaluation pipeline.")
    parser.add_argument(
        "--mode",
        choices=["query", "analyse", "both"],
        default="query",
        help="Which stage(s) to run.",
    )
    args = parser.parse_args()
    mode = args.mode

    if mode in {"query", "both"}:
        run_querying(
            prompts_path=config.EVALUATION_PROMPTS_PATH,
            system_prompt_path=config.EVALUATION_SYSTEM_PROMPT_PATH,
            output_path=config.QUERY_OUTPUT_PATH,
            models_override=config.EVAL_MODELS,
            skip_errors=config.SKIP_ERRORS,
            sequential=config.SEQUENTIAL,
        )

    if mode in {"analyse", "both"}:
        analysis_input = (
            config.QUERY_OUTPUT_PATH
            if mode == "both"
            else config.ANALYSIS_INPUT_CSV
        )
        run_yes_no_analysis(
            responses_csv=analysis_input,
            output_dir=config.ANALYSIS_OUTPUT_DIR,
            copy_readme_images=config.COPY_README_IMAGES,
        )


if __name__ == "__main__":
    main()
