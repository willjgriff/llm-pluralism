"""Mean persona rating score per persona_name from persona_responses.csv.

Reads results/persona_responses.csv and writes results/persona_score_means.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

PERSONA_RESPONSES_CSV_PATH = Path("results/persona_responses.csv")
PERSONA_SCORE_MEANS_JSON_PATH = Path("results/persona_score_means.json")


def main() -> None:
    """Load persona responses, compute mean score by persona, write JSON, print summary."""
    dataframe = pd.read_csv(PERSONA_RESPONSES_CSV_PATH)
    means = dataframe.groupby("persona_name")["score"].mean().round(2)
    records = [
        {"persona": str(persona_name), "mean_score": float(mean_score)}
        for persona_name, mean_score in means.items()
    ]
    records.sort(key=lambda row: row["persona"])

    PERSONA_SCORE_MEANS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PERSONA_SCORE_MEANS_JSON_PATH.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    print(f"Wrote {len(records)} persona means to {PERSONA_SCORE_MEANS_JSON_PATH}")
    for row in records:
        print(f"  {row['persona']}: {row['mean_score']}")


if __name__ == "__main__":
    main()
