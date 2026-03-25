"""CLI entrypoint for querying + analysis pipeline."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from model_interaction import run_querying
from result_analysis import run_yes_no_analysis


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run LLM query + analysis pipeline.")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["query", "analyse", "both"],
        default="query",
        help="Choose whether to run querying only, analysis only, or both.",
    )
    parser.add_argument(
        "--prompts",
        type=Path,
        default=Path("data/axis_prompts.csv"),
        help="Path to axis prompts CSV (axis, axis_name, prompt).",
    )
    parser.add_argument(
        "--system-prompt",
        type=Path,
        default=Path("data/response_system_prompt.txt"),
        help="Path to shared system prompt text file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/responses.csv"),
        help="Where to write responses CSV.",
    )
    parser.add_argument(
        "--models",
        type=str,
        default=os.getenv("EVAL_MODELS", ""),
        help="Comma-separated model specs like 'openai:gpt-4.1-mini,openrouter:meta-llama/llama-3.3-70b-instruct'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="If set > 0, only run the first N prompts.",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="If set, continue run when a model call fails and write error text to response.",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="If set, run models one after another instead of in parallel threads.",
    )
    parser.add_argument(
        "--copy-readme-images",
        action="store_true",
        help=(
            "After analysis, copy chart PNGs from the results directory to docs/images/ "
            "(for README). No effect when mode is query only."
        ),
    )
    parsed_args = parser.parse_args()

    if parsed_args.mode in {"query", "both"}:
        run_querying(
            prompts_path=parsed_args.prompts,
            system_prompt_path=parsed_args.system_prompt,
            output_path=parsed_args.output,
            models_override=parsed_args.models,
            limit=parsed_args.limit,
            skip_errors=parsed_args.skip_errors,
            sequential=parsed_args.sequential,
        )

    if parsed_args.mode in {"analyse", "both"}:
        analysis_input = parsed_args.output if parsed_args.mode == "both" else Path(
            "results/responses.csv"
        )
        run_yes_no_analysis(
            responses_csv=analysis_input,
            output_dir=Path("results"),
            copy_readme_images=parsed_args.copy_readme_images,
        )


if __name__ == "__main__":
    main()
