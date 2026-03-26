"""CLI entrypoint: behaviour is driven by ``config`` (and ``.env`` for keys)."""

from __future__ import annotations

import argparse

import config
from model_interaction import run_querying


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
        run_querying(
            prompts_path=config.EVALUATION_PROMPTS_PATH,
            system_prompt_path=config.EVALUATION_SYSTEM_PROMPT_PATH,
            output_path=config.QUERY_OUTPUT_PATH,
            models_override=config.EVAL_MODELS,
            skip_errors=config.SKIP_ERRORS,
            sequential=config.SEQUENTIAL,
        )

    if "persona_query" in selected_modes:
        pass

    if "analyse" in selected_modes:
        pass


if __name__ == "__main__":
    main()
