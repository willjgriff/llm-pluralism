"""CLI utility: inspect evaluation responses with persona ratings (not part of the main pipeline)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

import config


def _parse_comma_separated_ints(raw: str | None) -> list[int] | None:
    """Parse a comma-separated list of integers, or return None when unset/empty.

    Parameters:
        raw: String like ``\"13,14,15\"`` or None/empty.

    Returns:
        List of integers, or None when ``raw`` is falsy after strip.
    """
    if raw is None or not str(raw).strip():
        return None
    parts = [part.strip() for part in str(raw).split(",") if part.strip()]
    return [int(part) for part in parts]


def _load_merged_frame(
    *,
    response_model: str,
    question_ids: list[int] | None,
    persona_ids: list[int] | None,
    evaluation_path: Path,
    persona_path: Path,
) -> pd.DataFrame:
    """Load evaluation and persona CSVs, filter by model and optional questions/personas, inner-join.

    Parameters:
        response_model: Exact ``model`` / ``source_model`` label (e.g. ``openrouter:x-ai/grok-4-fast``).
        question_ids: If set, restrict to these ``question_id`` values.
        persona_ids: If set, restrict to these ``persona_id`` values.
        evaluation_path: Path to ``evaluation_responses.csv``.
        persona_path: Path to ``persona_responses.csv``.

    Returns:
        DataFrame with columns including ``question_id``, ``prompt``, ``response_model``,
        ``response_text``, ``persona_id``, ``persona_name``, ``score``, ``reasoning``.
    """
    eval_df = pd.read_csv(evaluation_path)
    persona_df = pd.read_csv(persona_path)

    model_key = response_model.strip()
    eval_df = eval_df[eval_df["model"].astype(str).str.strip() == model_key]
    persona_df = persona_df[persona_df["source_model"].astype(str).str.strip() == model_key]

    if question_ids is not None:
        eval_df = eval_df[eval_df["question_id"].isin(question_ids)]
        persona_df = persona_df[persona_df["question_id"].isin(question_ids)]

    if persona_ids is not None:
        persona_df = persona_df[persona_df["persona_id"].isin(persona_ids)]

    eval_df = eval_df.rename(
        columns={
            "model": "response_model",
            "question": "prompt",
            "response": "response_text",
        }
    )
    persona_df = persona_df.rename(columns={"response": "reasoning"})

    merged = persona_df.merge(
        eval_df[["question_id", "prompt", "response_model", "response_text"]],
        on="question_id",
        how="inner",
    )
    return merged.sort_values(["question_id", "persona_id"])


def _print_terminal(merged: pd.DataFrame) -> None:
    """Print one block per question with response body and persona rating subsections.

    Parameters:
        merged: Output of :func:`_load_merged_frame`.
    """
    for question_id, group in merged.groupby("question_id", sort=True):
        row0 = group.iloc[0]
        prompt = str(row0["prompt"])
        model = str(row0["response_model"])
        response_text = str(row0["response_text"])
        print("=" * 80)
        print(f"Question {question_id}: {prompt}")
        print(f"Model: {model}")
        print("-" * 80)
        print("RESPONSE:")
        print(response_text)
        print("-" * 80)
        print("PERSONA RATINGS:")
        for index, (_, pr) in enumerate(group.sort_values("persona_id").iterrows(), start=1):
            print(f"[{index}] {pr['persona_name']} — Score: {pr['score']}")
            print(pr["reasoning"])
            print()
        print("=" * 80)
        print()


def _write_csv(merged: pd.DataFrame, file) -> None:
    """Write one row per persona rating in the requested column order.

    Parameters:
        merged: Joined frame from :func:`_load_merged_frame`.
        file: File-like object (e.g. ``sys.stdout``).
    """
    out = merged[
        [
            "question_id",
            "prompt",
            "response_model",
            "response_text",
            "persona_id",
            "persona_name",
            "score",
            "reasoning",
        ]
    ]
    out.to_csv(file, index=False)


def main() -> None:
    """Parse CLI args, load data, and print terminal or CSV output plus a short summary."""
    parser = argparse.ArgumentParser(
        description="Inspect model responses and persona ratings from results CSVs."
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Response model label to filter (e.g. openrouter:x-ai/grok-4-fast).",
    )
    parser.add_argument(
        "--questions",
        default=None,
        help="Optional comma-separated question_ids (e.g. 13,14,15). Omit for all questions.",
    )
    parser.add_argument(
        "--personas",
        default=None,
        help="Optional comma-separated persona_ids (e.g. 1,2,5). Omit for all personas.",
    )
    parser.add_argument(
        "--output",
        choices=("terminal", "csv"),
        default="terminal",
        help="terminal: formatted blocks; csv: one row per persona rating.",
    )
    parser.add_argument(
        "--evaluation-path",
        type=Path,
        default=config.QUERY_OUTPUT_PATH,
        help="Path to evaluation_responses.csv (default: config.QUERY_OUTPUT_PATH).",
    )
    parser.add_argument(
        "--persona-path",
        type=Path,
        default=config.PERSONA_QUERY_OUTPUT_PATH,
        help="Path to persona_responses.csv (default: config.PERSONA_QUERY_OUTPUT_PATH).",
    )
    args = parser.parse_args()

    question_ids = _parse_comma_separated_ints(args.questions)
    persona_ids = _parse_comma_separated_ints(args.personas)
    merged = _load_merged_frame(
        response_model=args.model,
        question_ids=question_ids,
        persona_ids=persona_ids,
        evaluation_path=args.evaluation_path,
        persona_path=args.persona_path,
    )

    if merged.empty:
        print(
            "Summary: 0 response(s), 0 persona rating(s) returned (no matches).",
            file=sys.stderr,
        )
        return

    if args.output == "terminal":
        _print_terminal(merged)
    else:
        _write_csv(merged, sys.stdout)
    sys.stdout.flush()

    n_responses = merged["question_id"].nunique()
    n_ratings = len(merged)
    print(
        f"Summary: {n_responses} response(s), {n_ratings} persona rating(s) returned.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
