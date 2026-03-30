"""Inspect model responses and persona ratings from a persona_responses.csv file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas


def _import_config_module():
    """Import project config so defaults work when running from repository root."""
    try:
        import config  # type: ignore

        return config
    except ModuleNotFoundError:
        repository_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repository_root / "src"))
        import config  # type: ignore

        return config


config = _import_config_module()


def _parse_comma_separated_tokens(raw_value: str | None) -> list[str]:
    """Parse comma-separated CLI values into stripped tokens."""
    if raw_value is None or not str(raw_value).strip():
        return []
    return [token.strip() for token in str(raw_value).split(",") if token.strip()]


def _parse_optional_integer_list(raw_value: str | None) -> list[int] | None:
    """Parse comma-separated integers or return None when empty."""
    tokens = _parse_comma_separated_tokens(raw_value)
    if not tokens:
        return None
    return [int(token) for token in tokens]


def _parse_persona_filter(
    raw_persona_value: str | None,
) -> tuple[list[int] | None, bool]:
    """Parse persona filter and detect sentinel value 0."""
    persona_identifiers = _parse_optional_integer_list(raw_persona_value)
    if persona_identifiers is None:
        return None, False
    if persona_identifiers == [0]:
        return None, True
    return persona_identifiers, False


def _load_and_filter_persona_rows(
    *,
    persona_responses_path: Path,
    model_labels: list[str],
    question_identifiers: list[int] | None,
    persona_identifiers: list[int] | None,
    hide_persona_details: bool,
) -> pandas.DataFrame:
    """Read persona responses and apply model/question/persona filters."""
    persona_ratings_table = pandas.read_csv(persona_responses_path)
    filtered_table = persona_ratings_table[
        persona_ratings_table["source_model"].astype(str).str.strip().isin(model_labels)
    ]
    if question_identifiers is not None:
        filtered_table = filtered_table[
            filtered_table["question_id"].isin(question_identifiers)
        ]
    if hide_persona_details:
        filtered_table = filtered_table.drop_duplicates(
            subset=["question_id", "source_model"], keep="first"
        )
    elif persona_identifiers is not None:
        filtered_table = filtered_table[
            filtered_table["persona_id"].isin(persona_identifiers)
        ]
    renamed_table = filtered_table.rename(
        columns={
            "question": "prompt",
            "source_model": "response_model",
            "source_response": "response_text",
            "response": "reasoning",
        }
    )
    if hide_persona_details:
        renamed_table = renamed_table.assign(
            persona_id=pandas.NA,
            persona_name="",
            score="",
            reasoning="",
        )
    return renamed_table


def _attach_bridging_scores(
    *,
    response_table: pandas.DataFrame,
    bridging_scores_path: Path,
) -> pandas.DataFrame:
    """Left-join bridging_score on question_id and response_model."""
    if not bridging_scores_path.is_file():
        print(
            f"Warning: bridging scores file not found ({bridging_scores_path}); "
            "bridging_score will be blank.",
            file=sys.stderr,
        )
        return response_table.assign(bridging_score=pandas.NA)

    bridging_scores_table = (
        pandas.read_csv(bridging_scores_path)[
            ["question_id", "response_model", "bridging_score"]
        ]
        .assign(
            question_id=lambda table: table["question_id"].astype(str).str.strip(),
            response_model=lambda table: table["response_model"].astype(str).str.strip(),
        )
        .drop_duplicates(subset=["question_id", "response_model"])
    )
    normalized_response_table = response_table.assign(
        question_id=lambda table: table["question_id"].astype(str).str.strip(),
        response_model=lambda table: table["response_model"].astype(str).str.strip(),
    )
    return normalized_response_table.merge(
        bridging_scores_table, on=["question_id", "response_model"], how="left"
    )


def _sort_output_rows(response_table: pandas.DataFrame) -> pandas.DataFrame:
    """Sort rows by question_id, response_model, persona_id."""
    return response_table.sort_values(["question_id", "response_model", "persona_id"])


def _format_bridging_score(bridging_score_value) -> str:
    """Return terminal-safe bridging score text."""
    if pandas.isna(bridging_score_value):
        return "(not found)"
    return str(bridging_score_value)


def _print_terminal_blocks(
    response_table: pandas.DataFrame,
    *,
    hide_persona_details: bool,
) -> None:
    """Print one block per (question_id, response_model)."""
    for (
        question_identifier,
        response_model_label,
    ), grouped_table in response_table.groupby(["question_id", "response_model"], sort=True):
        first_row = grouped_table.iloc[0]
        print("=" * 80)
        print(f"Question {question_identifier}: {first_row['prompt']}")
        print(f"Model: {response_model_label}")
        print(f"Bridging score: {_format_bridging_score(first_row['bridging_score'])}")
        print("-" * 80)
        print("RESPONSE:")
        print(first_row["response_text"])
        print("-" * 80)
        if not hide_persona_details:
            print("PERSONA RATINGS:")
            for display_index, (_, persona_row) in enumerate(
                grouped_table.sort_values("persona_id").iterrows(), start=1
            ):
                print(
                    f"[{display_index}] {persona_row['persona_name']} — "
                    f"Score: {persona_row['score']}"
                )
                print(persona_row["reasoning"])
                print()
        print("=" * 80)
        print()


def _write_csv_to_stdout(response_table: pandas.DataFrame) -> None:
    """Write CSV output to stdout in required column order."""
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
    response_table[output_columns].to_csv(sys.stdout, index=False)


def _print_summary(
    response_table: pandas.DataFrame,
    *,
    hide_persona_details: bool,
) -> None:
    """Print summary counts to stderr."""
    response_block_count = int(
        response_table.groupby(["question_id", "response_model"], sort=False).ngroups
    )
    persona_rating_count = 0 if hide_persona_details else len(response_table)
    print(
        f"Summary: {response_block_count} response block(s), "
        f"{persona_rating_count} persona rating(s) returned.",
        file=sys.stderr,
    )


def _build_argument_parser() -> argparse.ArgumentParser:
    """Create CLI parser."""
    argument_parser = argparse.ArgumentParser(
        description="Inspect model responses and persona ratings from persona_responses.csv."
    )
    argument_parser.add_argument(
        "--model",
        required=True,
        help="Comma-separated source_model labels to filter by.",
    )
    argument_parser.add_argument(
        "--questions",
        default=None,
        help="Optional comma-separated question_ids to filter by.",
    )
    argument_parser.add_argument(
        "--personas",
        default=None,
        help=(
            "Optional comma-separated persona_ids to filter by, or single 0 to show only "
            "model responses with no persona details."
        ),
    )
    argument_parser.add_argument(
        "--output",
        choices=("terminal", "csv"),
        default="terminal",
        help='Output mode: "terminal" (default) or "csv".',
    )
    argument_parser.add_argument(
        "--persona-path",
        type=Path,
        default=config.PERSONA_QUERY_OUTPUT_PATH,
        help="Path to persona_responses.csv (default: config.PERSONA_QUERY_OUTPUT_PATH).",
    )
    argument_parser.add_argument(
        "--bridging-scores-path",
        type=Path,
        default=config.BRIDGING_SCORE_OUTPUT_PATH,
        help="Path to bridging_scores.csv (default: config.BRIDGING_SCORE_OUTPUT_PATH).",
    )
    return argument_parser


def main() -> None:
    """Run CLI utility."""
    parser = _build_argument_parser()
    arguments = parser.parse_args()

    model_labels = _parse_comma_separated_tokens(arguments.model)
    question_identifiers = _parse_optional_integer_list(arguments.questions)
    persona_identifiers, hide_persona_details = _parse_persona_filter(arguments.personas)

    response_table = _load_and_filter_persona_rows(
        persona_responses_path=arguments.persona_path,
        model_labels=model_labels,
        question_identifiers=question_identifiers,
        persona_identifiers=persona_identifiers,
        hide_persona_details=hide_persona_details,
    )
    response_table = _attach_bridging_scores(
        response_table=response_table,
        bridging_scores_path=arguments.bridging_scores_path,
    )
    response_table = _sort_output_rows(response_table)

    if response_table.empty:
        print(
            "Summary: 0 response block(s), 0 persona rating(s) returned (no matches).",
            file=sys.stderr,
        )
        return

    if arguments.output == "terminal":
        _print_terminal_blocks(response_table, hide_persona_details=hide_persona_details)
    else:
        _write_csv_to_stdout(response_table)
    sys.stdout.flush()
    _print_summary(response_table, hide_persona_details=hide_persona_details)


if __name__ == "__main__":
    main()
