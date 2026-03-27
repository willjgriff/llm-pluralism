"""Generate analysis charts from bridging and correlation CSV outputs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import colors

matplotlib.use("Agg")
import matplotlib.pyplot as plt

TITLE_SIZE = 12
LABEL_SIZE = 10
TICK_SIZE = 9
ANNOTATION_SIZE = 8
DPI = 150


def _read_bridging_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def _read_correlation_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def _mean_std(values: list[float]) -> tuple[float, float]:
    arr = np.array(values, dtype=float)
    return float(arr.mean()), float(arr.std(ddof=0))


def _chart_bridging_by_model(rows: list[dict[str, str]], output_path: Path) -> None:
    by_model: dict[str, list[float]] = {}
    for row in rows:
        model = row["response_model"]
        by_model.setdefault(model, []).append(float(row["bridging_score"]))

    models = sorted(by_model)
    means: list[float] = []
    stds: list[float] = []
    for model in models:
        mean_score, std_score = _mean_std(by_model[model])
        means.append(mean_score)
        stds.append(std_score)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(models, means, yerr=stds, capsize=4, color="#4C78A8")
    ax.set_title("Bridging Score by Model", fontsize=TITLE_SIZE)
    ax.set_ylabel("Mean Bridging Score", fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", labelrotation=20, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI)
    plt.close(fig)


def _chart_bridging_by_group(rows: list[dict[str, str]], output_path: Path) -> None:
    by_group: dict[str, list[float]] = {}
    for row in rows:
        group_name = row["group_name"]
        by_group.setdefault(group_name, []).append(float(row["bridging_score"]))

    groups = sorted(by_group)
    means: list[float] = []
    stds: list[float] = []
    for group_name in groups:
        mean_score, std_score = _mean_std(by_group[group_name])
        means.append(mean_score)
        stds.append(std_score)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(groups, means, yerr=stds, capsize=4, color="#72B7B2")
    ax.set_title("Bridging Score by Topic Group", fontsize=TITLE_SIZE)
    ax.set_ylabel("Mean Bridging Score", fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", labelrotation=35, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI)
    plt.close(fig)


def _chart_bridging_heatmap(rows: list[dict[str, str]], output_path: Path) -> None:
    models = sorted({row["response_model"] for row in rows})
    groups = sorted({row["group_name"] for row in rows})
    value_map = {
        (row["response_model"], row["group_name"]): float(row["bridging_score"])
        for row in rows
    }

    matrix = np.array(
        [[value_map[(model, group)] for group in groups] for model in models],
        dtype=float,
    )
    vmin = float(matrix.min())
    vmax = float(matrix.max())
    midpoint = (vmin + vmax) / 2.0
    norm = colors.TwoSlopeNorm(vmin=vmin, vcenter=midpoint, vmax=vmax)

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(matrix, cmap="coolwarm", norm=norm, aspect="auto")
    ax.set_title("Bridging Score by Model and Topic Group", fontsize=TITLE_SIZE)
    ax.set_xticks(np.arange(len(groups)), labels=groups)
    ax.set_yticks(np.arange(len(models)), labels=models)
    ax.tick_params(axis="x", labelrotation=35, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color="black",
                fontsize=ANNOTATION_SIZE,
            )

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI)
    plt.close(fig)


def _chart_persona_correlation_heatmap(
    rows: list[dict[str, str]], output_path: Path
) -> None:
    persona_ids = sorted(
        {
            int(row["persona_a_id"])
            for row in rows
        }
        | {
            int(row["persona_b_id"])
            for row in rows
        }
    )
    name_by_id: dict[int, str] = {}
    for row in rows:
        name_by_id[int(row["persona_a_id"])] = row["persona_a_name"]
        name_by_id[int(row["persona_b_id"])] = row["persona_b_name"]

    index_by_id = {persona_id: i for i, persona_id in enumerate(persona_ids)}
    matrix = np.eye(len(persona_ids), dtype=float)
    for row in rows:
        a_id = int(row["persona_a_id"])
        b_id = int(row["persona_b_id"])
        corr = float(row["correlation"])
        i = index_by_id[a_id]
        j = index_by_id[b_id]
        matrix[i, j] = corr
        matrix[j, i] = corr

    labels = [name_by_id[persona_id] for persona_id in persona_ids]
    norm = colors.TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(matrix, cmap="coolwarm", norm=norm, aspect="equal")
    ax.set_title("Persona Rating Correlations", fontsize=TITLE_SIZE)
    ax.set_xticks(np.arange(len(labels)), labels=labels)
    ax.set_yticks(np.arange(len(labels)), labels=labels)
    ax.tick_params(axis="x", labelrotation=35, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color="black",
                fontsize=ANNOTATION_SIZE,
            )

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI)
    plt.close(fig)


def generate_analysis_charts(
    *,
    bridging_scores_csv: Path,
    persona_correlations_csv: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    bridging_rows = _read_bridging_rows(bridging_scores_csv)
    correlation_rows = _read_correlation_rows(persona_correlations_csv)

    _chart_bridging_by_model(
        bridging_rows, output_dir / "bridging_scores_by_model.png"
    )
    _chart_bridging_by_group(
        bridging_rows, output_dir / "bridging_scores_by_group.png"
    )
    _chart_bridging_heatmap(
        bridging_rows, output_dir / "bridging_scores_by_model_and_group.png"
    )
    _chart_persona_correlation_heatmap(
        correlation_rows, output_dir / "persona_correlations.png"
    )

    print(f"[analyse] Wrote charts to {output_dir}")
