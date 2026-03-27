"""Generate analysis charts from bridging and correlation CSV outputs."""

from __future__ import annotations

import csv
from collections.abc import Callable
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib import colors

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
from result_analysis.scoring.bridging_score import LAMBDA_VALUES

TITLE_SIZE = 12
LABEL_SIZE = 10
TICK_SIZE = 9
ANNOTATION_SIZE = 8
DPI = 150


def _read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as input_file:
        return list(csv.DictReader(input_file))


def _save_and_close(
    fig: plt.Figure,
    output_path: Path,
    *,
    tight_layout_rect: tuple[float, float, float, float] | None = None,
    after_tight_layout: Callable[[plt.Figure], None] | None = None,
    subplots_adjust_kwargs: dict[str, float] | None = None,
) -> None:
    """Lay out the figure, optionally run a hook (e.g. footnotes), then save and close.

    Parameters:
        fig: Matplotlib figure to save.
        output_path: Destination PNG path.
        tight_layout_rect: Optional ``(left, bottom, right, top)`` in figure coordinates
            passed to ``tight_layout(rect=...)`` to reserve margin space.
        after_tight_layout: Optional callback invoked after ``tight_layout`` to add
            elements such as figure-level footnotes in reserved margins.
        subplots_adjust_kwargs: Optional keyword arguments for ``fig.subplots_adjust``,
            applied after ``tight_layout`` (e.g. ``{"bottom": 0.22}`` for extra margin).
    """
    if tight_layout_rect is None:
        fig.tight_layout()
    else:
        fig.tight_layout(rect=tight_layout_rect)
    if after_tight_layout is not None:
        after_tight_layout(fig)
    if subplots_adjust_kwargs is not None:
        fig.subplots_adjust(**subplots_adjust_kwargs)
    fig.savefig(output_path, dpi=DPI)
    plt.close(fig)


def _save_figure_with_footnote_below_x_axis(
    fig: plt.Figure,
    ax: plt.Axes,
    footnote: str,
    output_path: Path,
) -> None:
    """Lay out the figure, add a footnote fully below x tick labels and xlabel, then save.

    Uses a renderer pass to measure label bboxes in figure coordinates so the note does not
    overlap rotated tick text, while keeping extra bottom margin modest.

    Parameters:
        fig: Figure containing ``ax``.
        ax: Axes whose x tick labels and x-axis label sit above the footnote.
        footnote: Text to draw in small italic, left-aligned under the axis decorations.
        output_path: PNG path to write.
    """
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.36)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_inv = fig.transFigure.inverted()
    label_bboxes = [
        label.get_window_extent(renderer=renderer).transformed(fig_inv)
        for label in ax.get_xticklabels()
    ]
    xlabel_bbox = ax.xaxis.label.get_window_extent(renderer=renderer).transformed(fig_inv)
    lowest_y0 = min(bbox.y0 for bbox in (*label_bboxes, xlabel_bbox))
    gap = 0.012
    fig.text(
        0.03,
        lowest_y0 - gap,
        footnote,
        transform=fig.transFigure,
        fontsize=7,
        style="italic",
        ha="left",
        va="top",
        wrap=True,
    )
    fig.savefig(output_path, dpi=DPI)
    plt.close(fig)


def _color_by_model(models: list[str]) -> dict[str, tuple[float, float, float, float]]:
    cmap = plt.get_cmap("tab10")
    return {model: cmap(i % 10) for i, model in enumerate(models)}


def _annotate_heatmap_values(ax: plt.Axes, matrix: np.ndarray) -> None:
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
    _save_and_close(fig, output_path)


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
    _save_and_close(fig, output_path)


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

    _annotate_heatmap_values(ax, matrix)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _save_and_close(fig, output_path)


def _chart_mean_vs_std_scatter(rows: list[dict[str, str]], output_path: Path) -> None:
    models = sorted({row["response_model"] for row in rows})
    color_by_model = _color_by_model(models)

    fig, ax = plt.subplots(figsize=(10, 6))
    for model in models:
        model_rows = [row for row in rows if row["response_model"] == model]
        x_vals = [float(row["mean_score"]) for row in model_rows]
        y_vals = [float(row["std_score"]) for row in model_rows]
        ax.scatter(
            x_vals,
            y_vals,
            label=model,
            color=color_by_model[model],
            alpha=0.8,
            edgecolors="white",
            linewidths=0.5,
            s=60,
        )

    ax.set_title("Mean vs Std Dev of Persona Scores by Response", fontsize=TITLE_SIZE)
    ax.set_xlabel("Mean Score", fontsize=LABEL_SIZE)
    ax.set_ylabel("Score Std Deviation", fontsize=LABEL_SIZE)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(fontsize=TICK_SIZE)
    ax.tick_params(axis="both", labelsize=TICK_SIZE)
    _save_and_close(fig, output_path)


def _chart_persona_score_distributions(
    rows: list[dict[str, str]], output_path: Path
) -> None:
    persona_ids = config.ANALYSIS_PERSONA_IDS
    scores_by_persona: dict[int, list[float]] = {pid: [] for pid in persona_ids}
    names_by_persona: dict[int, str] = {}

    for row in rows:
        persona_id = int(row["persona_id"])
        if persona_id not in scores_by_persona:
            continue
        scores_by_persona[persona_id].append(float(row["score"].strip()))
        names_by_persona[persona_id] = row["persona_name"].strip()

    persona_ids_present = [pid for pid in persona_ids if scores_by_persona[pid]]
    labels = [names_by_persona[pid] for pid in persona_ids_present]
    series = [scores_by_persona[pid] for pid in persona_ids_present]

    footnote = (
        "Note: Communitarian Nationalist outlier circles represent all non-median scores "
        "due to IQR compression around 3, not rare individual occurrences."
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(series, labels=labels, patch_artist=True)
    ax.set_title("Score Distribution by Persona", fontsize=TITLE_SIZE)
    ax.set_xlabel("Persona", fontsize=LABEL_SIZE)
    ax.set_ylabel("Score (1-5)", fontsize=LABEL_SIZE)
    ax.set_ylim(1, 5)
    ax.tick_params(axis="x", labelrotation=25, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    ax.grid(True, axis="y", linestyle="--", alpha=0.3)

    _save_figure_with_footnote_below_x_axis(fig, ax, footnote, output_path)


def _chart_bridging_scores_ranked(rows: list[dict[str, str]], output_path: Path) -> None:
    sorted_rows = sorted(rows, key=lambda row: float(row["bridging_score"]), reverse=True)
    models = sorted({row["response_model"] for row in sorted_rows})
    color_by_model = _color_by_model(models)

    def _short_label(row: dict[str, str]) -> str:
        prompt = row["prompt"].strip()
        prompt_short = (prompt[:40] + "...") if len(prompt) > 40 else prompt
        return f"{row['response_model']} | {prompt_short}"

    labels = [_short_label(row) for row in sorted_rows]
    values = [float(row["bridging_score"]) for row in sorted_rows]
    bar_colors = [color_by_model[row["response_model"]] for row in sorted_rows]

    fig_height = max(8, len(sorted_rows) * 0.28)
    fig, ax = plt.subplots(figsize=(14, fig_height))
    y_positions = np.arange(len(sorted_rows))
    ax.barh(y_positions, values, color=bar_colors)
    ax.set_yticks(y_positions, labels=labels)
    ax.invert_yaxis()
    ax.set_title("Bridging Scores Ranked by Response", fontsize=TITLE_SIZE)
    ax.set_xlabel("Bridging Score", fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(True, axis="x", linestyle="--", alpha=0.3)

    legend_handles = [
        plt.Line2D([0], [0], marker="s", linestyle="", color=color_by_model[model], label=model)
        for model in models
    ]
    ax.legend(handles=legend_handles, fontsize=TICK_SIZE, loc="lower right")

    _save_and_close(fig, output_path)


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

    _annotate_heatmap_values(ax, matrix)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _save_and_close(fig, output_path)


def _chart_lambda_comparison(rows: list[dict[str, str]], output_path: Path) -> None:
    models = sorted({row["response_model"] for row in rows})
    lambda_columns = [f"bridging_score_{lambda_value:.2f}" for lambda_value in LAMBDA_VALUES]

    fig, ax = plt.subplots(figsize=(10, 5))
    x_values = np.arange(len(models), dtype=float)
    number_of_lambdas = len(LAMBDA_VALUES)
    bar_width = 0.22
    bar_colors = ["#4C78A8", "#F58518", "#54A24B"]

    for lambda_index, lambda_value in enumerate(LAMBDA_VALUES):
        lambda_column = lambda_columns[lambda_index]
        mean_values: list[float] = []
        std_values: list[float] = []
        for model in models:
            values = [
                float(row[lambda_column])
                for row in rows
                if row["response_model"] == model
            ]
            mean_value, std_value = _mean_std(values)
            mean_values.append(mean_value)
            std_values.append(std_value)

        x_offset = (lambda_index - (number_of_lambdas - 1) / 2.0) * bar_width
        ax.bar(
            x_values + x_offset,
            mean_values,
            bar_width,
            yerr=std_values,
            capsize=4,
            label=f"λ={lambda_value:.2f}",
            color=bar_colors[lambda_index % len(bar_colors)],
        )

    ax.set_xticks(x_values)
    ax.set_xticklabels(models, rotation=20)
    ax.set_ylabel("Mean Bridging Score", fontsize=LABEL_SIZE)
    ax.set_title("Model Bridging Scores Across Lambda Values", fontsize=TITLE_SIZE)
    ax.legend(fontsize=TICK_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    _save_and_close(fig, output_path)


def generate_analysis_charts(
    *,
    bridging_scores_csv: Path,
    persona_correlations_csv: Path,
    persona_ratings_csv: Path,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    bridging_rows = _read_csv_rows(bridging_scores_csv)
    correlation_rows = _read_csv_rows(persona_correlations_csv)
    persona_rating_rows = _read_csv_rows(persona_ratings_csv)

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
    _chart_mean_vs_std_scatter(
        bridging_rows, output_dir / "mean_vs_std_scatter.png"
    )
    _chart_persona_score_distributions(
        persona_rating_rows, output_dir / "persona_score_distributions.png"
    )
    _chart_bridging_scores_ranked(
        bridging_rows, output_dir / "bridging_scores_ranked.png"
    )
    _chart_lambda_comparison(
        bridging_rows, output_dir / "bridging_scores_lambda_comparison.png"
    )

    print(f"[analyse] Wrote charts to {output_dir}")
