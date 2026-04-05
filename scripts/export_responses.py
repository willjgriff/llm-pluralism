"""Export evaluation responses to a JSON file suitable for serving from a website backend.

Reads from docs/run_1/output/evaluation_responses.csv and
docs/run_1/data/evaluation_prompts.csv, then writes a flat JSON array to
output/scripts/web_formatted_responses.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas

RESPONSES_CSV_PATH = Path("output/evaluation_responses.csv")
PROMPTS_CSV_PATH = Path("data/evaluation_prompts.csv")
OUTPUT_JSON_PATH = Path("output/scripts/web_formatted_responses.json")


def _import_config_module():
    """Import the project config module, adding src/ to sys.path if needed.

    Returns
    -------
    module
        The imported config module.
    """
    try:
        import config  # type: ignore

        return config
    except ModuleNotFoundError:
        repository_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repository_root / "src"))
        import config  # type: ignore

        return config


_config = _import_config_module()
MODEL_DISPLAY_NAMES: dict[str, str] = _config.MODEL_DISPLAY_NAMES


def _group_name_to_slug(group_name: str) -> str:
    """Convert a human-readable group name to a lowercase underscore slug.

    Parameters
    ----------
    group_name:
        The display name, e.g. ``"Economic redistribution"``.

    Returns
    -------
    str
        Slug form, e.g. ``"economic_redistribution"``.
    """
    return group_name.strip().lower().replace(" ", "_")


def _load_prompts(prompts_csv_path: Path) -> dict[int, dict[str, str]]:
    """Load prompts CSV and index it by question_id.

    Parameters
    ----------
    prompts_csv_path:
        Path to the evaluation_prompts.csv file.

    Returns
    -------
    dict
        Mapping from ``question_id`` (int) to a dict with keys
        ``"group_id"``, ``"group_name"``, and ``"prompt"``.
    """
    prompts_table = pandas.read_csv(prompts_csv_path)
    return {
        int(row["question_id"]): {
            "group_id": int(row["group_id"]),
            "group_name": str(row["group_name"]),
            "prompt": str(row["prompt"]),
        }
        for _, row in prompts_table.iterrows()
    }


def _build_response_records(
    responses_table: pandas.DataFrame,
    prompts_by_id: dict[int, dict[str, str]],
) -> list[dict]:
    """Build the list of JSON-ready response records.

    Parameters
    ----------
    responses_table:
        DataFrame loaded from evaluation_responses.csv.
    prompts_by_id:
        Prompt metadata indexed by question_id.

    Returns
    -------
    list[dict]
        One dict per response row, with all required fields.
    """
    records = []
    for _, row in responses_table.iterrows():
        question_id = int(row["question_id"])
        model = str(row["model"])
        prompt_meta = prompts_by_id[question_id]
        group_name = prompt_meta["group_name"]

        records.append(
            {
                "question_id": question_id,
                "group": _group_name_to_slug(group_name),
                "group_name": group_name,
                "prompt": prompt_meta["prompt"],
                "model": model,
                "model_display_name": MODEL_DISPLAY_NAMES.get(model, model),
                "response_text": str(row["response"]),
            }
        )
    return records


def _print_summary(records: list[dict]) -> None:
    """Print a breakdown of exported responses per model and per question group.

    Parameters
    ----------
    records:
        The exported response records.
    """
    print(f"\nTotal responses exported: {len(records)}")

    model_counts: dict[str, int] = {}
    group_counts: dict[str, int] = {}
    for record in records:
        model_counts[record["model_display_name"]] = (
            model_counts.get(record["model_display_name"], 0) + 1
        )
        group_counts[record["group_name"]] = (
            group_counts.get(record["group_name"], 0) + 1
        )

    print("\nResponses per model:")
    for model_name, count in sorted(model_counts.items()):
        print(f"  {model_name}: {count}")

    print("\nResponses per question group:")
    for group_name, count in sorted(group_counts.items()):
        print(f"  {group_name}: {count}")


def main() -> None:
    """Load evaluation responses and prompts, then write web_formatted_responses.json."""
    prompts_by_id = _load_prompts(PROMPTS_CSV_PATH)
    responses_table = pandas.read_csv(RESPONSES_CSV_PATH)

    records = _build_response_records(responses_table, prompts_by_id)

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, indent=2, ensure_ascii=False)

    print(f"Exported {len(records)} responses to {OUTPUT_JSON_PATH}")
    _print_summary(records)

    expected_total = 54
    if len(records) != expected_total:
        print(
            f"\nWarning: expected {expected_total} responses but got {len(records)}.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
