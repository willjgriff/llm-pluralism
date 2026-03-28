"""CLI utility: inspect model responses and persona ratings from persona_responses.csv only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas

import config


def _parse_comma_separated_integers(raw_string: str | None) -> list[int] | None:
    """Parse a comma-separated list of integers, or return None when unset/empty.

    Parameters:
        raw_string: String like ``\"13,14,15\"`` or None/empty.

    Returns:
        List of integers, or None when ``raw_string`` is falsy after strip.
    """
    if raw_string is None or not str(raw_string).strip():
        return None
    stripped_tokens = [
        token.strip() for token in str(raw_string).split(",") if token.strip()
    ]
    return [int(token) for token in stripped_tokens]


def _parse_comma_separated_model_labels(raw_string: str) -> list[str]:
    """Parse comma-separated response model labels (``source_model`` values), stripped.

    Parameters:
        raw_string: String like ``\"openai:gpt-4.1-mini,openrouter:...\"``.

    Returns:
        Non-empty list of model label strings.
    """
    stripped_tokens = [
        token.strip() for token in str(raw_string).split(",") if token.strip()
    ]
    return stripped_tokens


def _parse_personas_filter(
    raw_string: str | None,
) -> tuple[list[int] | None, bool]:
    """Parse ``--personas``: optional ID list, or sentinel ``0`` meaning omit persona output.

    Parameters:
        raw_string: Same as ``--personas`` CLI value.

    Returns:
        ``(persona_identifiers, omit_persona_rating_details)``. When the value is exactly
        ``0`` (single token), returns ``(None, True)`` — no persona rows in output, only
        model responses. Otherwise ``omit_persona_rating_details`` is False and
        ``persona_identifiers`` is None (all personas) or a non-empty list of IDs.
    """
    if raw_string is None or not str(raw_string).strip():
        return None, False
    persona_identifiers = _parse_comma_separated_integers(raw_string)
    if persona_identifiers is None:
        return None, False
    if len(persona_identifiers) == 1 and persona_identifiers[0] == 0:
        return None, True
    return persona_identifiers, False


def _merge_bridging_scores_column(
    persona_ratings_dataframe: pandas.DataFrame,
    bridging_scores_csv_path: Path,
) -> pandas.DataFrame:
    """Left-join ``bridging_score`` from ``bridging_scores.csv`` on ``question_id`` and ``response_model``.

    Parameters:
        persona_ratings_dataframe: Frame with ``question_id`` and ``response_model`` columns.
        bridging_scores_csv_path: Path to analysis bridging scores CSV.

    Returns:
        Copy of the frame with a ``bridging_score`` column (NA when no file or no matching row).
    """
    result_dataframe = persona_ratings_dataframe.copy()
    if not bridging_scores_csv_path.is_file():
        print(
            f"Note: bridging scores file not found ({bridging_scores_csv_path}); "
            "bridging_score will be blank.",
            file=sys.stderr,
        )
        result_dataframe["bridging_score"] = pandas.NA
        return result_dataframe

    bridging_scores_dataframe = pandas.read_csv(bridging_scores_csv_path)
    bridge_subset = bridging_scores_dataframe[
        ["question_id", "response_model", "bridging_score"]
    ].copy()
    bridge_subset["__merge_question_id"] = (
        bridge_subset["question_id"].astype(str).str.strip()
    )
    bridge_subset["__merge_response_model"] = (
        bridge_subset["response_model"].astype(str).str.strip()
    )
    bridge_subset = bridge_subset.drop_duplicates(
        subset=["__merge_question_id", "__merge_response_model"]
    )
    bridge_subset = bridge_subset[
        ["__merge_question_id", "__merge_response_model", "bridging_score"]
    ]

    result_dataframe["__merge_question_id"] = (
        result_dataframe["question_id"].astype(str).str.strip()
    )
    result_dataframe["__merge_response_model"] = (
        result_dataframe["response_model"].astype(str).str.strip()
    )
    merged_dataframe = result_dataframe.merge(
        bridge_subset,
        on=["__merge_question_id", "__merge_response_model"],
        how="left",
    )
    return merged_dataframe.drop(
        columns=["__merge_question_id", "__merge_response_model"]
    )


def _format_bridging_score_for_terminal(bridging_score_value) -> str:
    """Format a bridging score cell for terminal output, or a placeholder when missing.

    Parameters:
        bridging_score_value: Scalar from ``bridging_score`` column (may be NA).

    Returns:
        Human-readable string for the header block.
    """
    if pandas.isna(bridging_score_value):
        return "(not found in bridging scores file)"
    return str(bridging_score_value).strip()


def _load_persona_ratings_dataframe(
    *,
    response_model_labels: list[str],
    question_identifiers: list[int] | None,
    persona_identifiers: list[int] | None,
    omit_persona_rating_details: bool,
    persona_responses_path: Path,
) -> pandas.DataFrame:
    """Load persona ratings, filter by models and optional questions/personas, normalize columns.

    Uses ``question``, ``source_model``, ``source_response``, and ``response`` from the CSV
    as ``prompt``, ``response_model``, ``response_text``, and ``reasoning`` respectively.

    Parameters:
        response_model_labels: Exact ``source_model`` labels to include (one or more).
        question_identifiers: If set, restrict to these ``question_id`` values.
        persona_identifiers: If set, restrict to these ``persona_id`` values (ignored when
            ``omit_persona_rating_details`` is True).
        omit_persona_rating_details: If True, one row per ``(question_id, source_model)``
            with prompt and response only; persona fields cleared.
        persona_responses_path: Path to ``persona_responses.csv``.

    Returns:
        DataFrame sorted by ``question_id``, ``response_model``, ``persona_id`` with columns
        including ``question_id``, ``prompt``, ``response_model``, ``response_text``,
        ``persona_id``, ``persona_name``, ``score``, ``reasoning``.
    """
    persona_ratings_dataframe = pandas.read_csv(persona_responses_path)
    normalized_model_labels = [label.strip() for label in response_model_labels]
    filtered_dataframe = persona_ratings_dataframe[
        persona_ratings_dataframe["source_model"]
        .astype(str)
        .str.strip()
        .isin(normalized_model_labels)
    ]

    if question_identifiers is not None:
        filtered_dataframe = filtered_dataframe[
            filtered_dataframe["question_id"].isin(question_identifiers)
        ]

    if omit_persona_rating_details:
        filtered_dataframe = filtered_dataframe.drop_duplicates(
            subset=["question_id", "source_model"], keep="first"
        )
    elif persona_identifiers is not None:
        filtered_dataframe = filtered_dataframe[
            filtered_dataframe["persona_id"].isin(persona_identifiers)
        ]

    normalized_dataframe = filtered_dataframe.rename(
        columns={
            "question": "prompt",
            "source_model": "response_model",
            "source_response": "response_text",
            "response": "reasoning",
        }
    )

    if omit_persona_rating_details:
        normalized_dataframe = normalized_dataframe.copy()
        normalized_dataframe["persona_id"] = pandas.NA
        normalized_dataframe["persona_name"] = ""
        normalized_dataframe["score"] = ""
        normalized_dataframe["reasoning"] = ""

    sort_columns = ["question_id", "response_model", "persona_id"]
    return normalized_dataframe.sort_values(sort_columns)


def _print_terminal_output(
    persona_ratings_dataframe: pandas.DataFrame,
    *,
    omit_persona_rating_details: bool,
) -> None:
    """Print one block per (question, model) with response body and optional persona lines.

    Parameters:
        persona_ratings_dataframe: Filtered persona ratings with normalized column names.
        omit_persona_rating_details: If True, skip persona rating subsection entirely.
    """
    grouping_columns = ["question_id", "response_model"]
    for group_keys, ratings_group_dataframe in persona_ratings_dataframe.groupby(
        grouping_columns, sort=True
    ):
        question_identifier, response_model_label = group_keys
        first_row = ratings_group_dataframe.iloc[0]
        prompt_text = str(first_row["prompt"])
        model_response_text = str(first_row["response_text"])
        bridging_score_display = _format_bridging_score_for_terminal(
            first_row["bridging_score"]
        )
        print("=" * 80)
        print(f"Question {question_identifier}: {prompt_text}")
        print(f"Model: {response_model_label}")
        print(f"Bridging score: {bridging_score_display}")
        print("-" * 80)
        print("RESPONSE:")
        print(model_response_text)
        print("-" * 80)
        if omit_persona_rating_details:
            print("=" * 80)
            print()
            continue
        print("PERSONA RATINGS:")
        sorted_group = ratings_group_dataframe.sort_values("persona_id")
        for display_index, (_, persona_rating_row) in enumerate(
            sorted_group.iterrows(), start=1
        ):
            persona_name = persona_rating_row["persona_name"]
            score_value = persona_rating_row["score"]
            reasoning_text = persona_rating_row["reasoning"]
            print(f"[{display_index}] {persona_name} — Score: {score_value}")
            print(reasoning_text)
            print()
        print("=" * 80)
        print()


def _write_csv_output(
    persona_ratings_dataframe: pandas.DataFrame,
    output_file,
) -> None:
    """Write CSV: one row per persona rating, or one row per response when personas omitted.

    Parameters:
        persona_ratings_dataframe: Filtered persona ratings with normalized column names.
        output_file: File-like object (e.g. ``sys.stdout``).
    """
    output_columns = [
        "question_id",
        "prompt",
        "response_model",
        "bridging_score",
        "response_text",
        "persona_id",
        "persona_name",
        "score",
        "reasoning",
    ]
    output_dataframe = persona_ratings_dataframe[output_columns]
    output_dataframe.to_csv(output_file, index=False)


def main() -> None:
    """Parse CLI arguments, load persona ratings, print terminal or CSV output and a summary."""
    argument_parser = argparse.ArgumentParser(
        description="Inspect model responses and persona ratings from persona_responses.csv."
    )
    argument_parser.add_argument(
        "--model",
        required=True,
        dest="response_models_filter_string",
        help=(
            "Comma-separated response model labels (source_model), "
            "e.g. openai:gpt-4.1-mini,openrouter:x-ai/grok-4-fast."
        ),
    )
    argument_parser.add_argument(
        "--questions",
        default=None,
        dest="questions_filter_string",
        help="Optional comma-separated question_ids (e.g. 13,14,15). Omit for all questions.",
    )
    argument_parser.add_argument(
        "--personas",
        default=None,
        dest="personas_filter_string",
        help=(
            "Optional comma-separated persona_ids (e.g. 1,2,5), or single 0 to show only "
            "model responses with no persona lines. Omit for all personas."
        ),
    )
    argument_parser.add_argument(
        "--output",
        choices=("terminal", "csv"),
        default="terminal",
        dest="output_format",
        help="terminal: formatted blocks; csv: one row per persona rating (or per response if --personas 0).",
    )
    argument_parser.add_argument(
        "--persona-path",
        type=Path,
        dest="persona_responses_path",
        default=config.PERSONA_QUERY_OUTPUT_PATH,
        help="Path to persona_responses.csv (default: config.PERSONA_QUERY_OUTPUT_PATH).",
    )
    argument_parser.add_argument(
        "--bridging-scores-path",
        type=Path,
        dest="bridging_scores_csv_path",
        default=config.BRIDGING_SCORE_OUTPUT_PATH,
        help=(
            "Path to bridging_scores.csv (default: config.BRIDGING_SCORE_OUTPUT_PATH, "
            "typically results/analysis/bridging_scores.csv)."
        ),
    )
    parsed_arguments = argument_parser.parse_args()

    response_model_labels = _parse_comma_separated_model_labels(
        parsed_arguments.response_models_filter_string
    )
    question_identifiers = _parse_comma_separated_integers(
        parsed_arguments.questions_filter_string
    )
    persona_identifiers, omit_persona_rating_details = _parse_personas_filter(
        parsed_arguments.personas_filter_string
    )

    persona_ratings_dataframe = _load_persona_ratings_dataframe(
        response_model_labels=response_model_labels,
        question_identifiers=question_identifiers,
        persona_identifiers=persona_identifiers,
        omit_persona_rating_details=omit_persona_rating_details,
        persona_responses_path=parsed_arguments.persona_responses_path,
    )
    persona_ratings_dataframe = _merge_bridging_scores_column(
        persona_ratings_dataframe,
        parsed_arguments.bridging_scores_csv_path,
    )

    if persona_ratings_dataframe.empty:
        print(
            "Summary: 0 response(s), 0 persona rating(s) returned (no matches).",
            file=sys.stderr,
        )
        return

    if parsed_arguments.output_format == "terminal":
        _print_terminal_output(
            persona_ratings_dataframe,
            omit_persona_rating_details=omit_persona_rating_details,
        )
    else:
        _write_csv_output(persona_ratings_dataframe, sys.stdout)
    sys.stdout.flush()

    number_of_response_blocks = int(
        persona_ratings_dataframe.groupby(
            ["question_id", "response_model"], sort=False
        ).ngroups
    )
    if omit_persona_rating_details:
        number_of_persona_ratings_returned = 0
    else:
        number_of_persona_ratings_returned = len(persona_ratings_dataframe)
    print(
        f"Summary: {number_of_response_blocks} response(s), "
        f"{number_of_persona_ratings_returned} persona rating(s) returned.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
