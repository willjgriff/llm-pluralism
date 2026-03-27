"""Charts derived from bridging score CSV rows."""

from __future__ import annotations

from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

from result_analysis.charts.figure_utils import save_and_close
from result_analysis.charts.plot_utils import (
    color_by_model,
    mean_std,
    save_bar_chart_with_error_bars,
    save_heatmap_with_colorbar,
)
from result_analysis.charts.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.scoring.bridging_score import LAMBDA_VALUES


def chart_bridging_by_model(rows: list[dict[str, str]], output_path: Path) -> None:
    """Bar chart: mean bridging score per ``response_model`` with std across prompts."""
    by_model: dict[str, list[float]] = {}
    for row in rows:
        model = row["response_model"]
        by_model.setdefault(model, []).append(float(row["bridging_score"]))

    models = sorted(by_model)
    means = []
    stds = []
    for model in models:
        mean_val, std_val = mean_std(by_model[model])
        means.append(mean_val)
        stds.append(std_val)

    save_bar_chart_with_error_bars(
        categories=models,
        means=means,
        stds=stds,
        color="#4C78A8",
        title="Bridging Score by Model",
        ylabel="Mean Bridging Score",
        x_rotation=20,
        output_path=output_path,
    )


def chart_bridging_by_group(rows: list[dict[str, str]], output_path: Path) -> None:
    """Bar chart: mean bridging score per ``group_name`` with std across rows."""
    by_group: dict[str, list[float]] = {}
    for row in rows:
        group_name = row["group_name"]
        by_group.setdefault(group_name, []).append(float(row["bridging_score"]))

    groups = sorted(by_group)
    means = []
    stds = []
    for group_name in groups:
        mean_val, std_val = mean_std(by_group[group_name])
        means.append(mean_val)
        stds.append(std_val)

    save_bar_chart_with_error_bars(
        categories=groups,
        means=means,
        stds=stds,
        color="#72B7B2",
        title="Bridging Score by Topic Group",
        ylabel="Mean Bridging Score",
        x_rotation=35,
        output_path=output_path,
    )


def chart_bridging_heatmap(rows: list[dict[str, str]], output_path: Path) -> None:
    """Heatmap: bridging score for each model × topic group (diverging norm from data range)."""
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

    save_heatmap_with_colorbar(
        matrix=matrix,
        row_labels=models,
        col_labels=groups,
        norm=norm,
        title="Bridging Score by Model and Topic Group",
        xlabel=None,
        ylabel=None,
        output_path=output_path,
        figsize=(10, 5),
        aspect="auto",
        x_tick_rotation=35,
    )


def chart_mean_vs_std_scatter(rows: list[dict[str, str]], output_path: Path) -> None:
    """Scatter: ``mean_score`` vs ``std_score`` per response, coloured by model."""
    models = sorted({row["response_model"] for row in rows})
    colors_map = color_by_model(models)

    fig, ax = plt.subplots(figsize=(10, 6))
    for model in models:
        model_rows = [row for row in rows if row["response_model"] == model]
        x_vals = [float(row["mean_score"]) for row in model_rows]
        y_vals = [float(row["std_score"]) for row in model_rows]
        ax.scatter(
            x_vals,
            y_vals,
            label=model,
            color=colors_map[model],
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
    save_and_close(fig, output_path)


def chart_bridging_scores_ranked(rows: list[dict[str, str]], output_path: Path) -> None:
    """Horizontal bars: all responses ranked by ``bridging_score`` (highest at top)."""
    sorted_rows = sorted(rows, key=lambda row: float(row["bridging_score"]), reverse=True)
    models = sorted({row["response_model"] for row in sorted_rows})
    colors_map = color_by_model(models)

    def short_label(row: dict[str, str]) -> str:
        prompt = row["prompt"].strip()
        prompt_short = (prompt[:40] + "...") if len(prompt) > 40 else prompt
        return f"{row['response_model']} | {prompt_short}"

    labels = [short_label(row) for row in sorted_rows]
    values = [float(row["bridging_score"]) for row in sorted_rows]
    bar_colors = [colors_map[row["response_model"]] for row in sorted_rows]

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
        plt.Line2D([0], [0], marker="s", linestyle="", color=colors_map[model], label=model)
        for model in models
    ]
    ax.legend(handles=legend_handles, fontsize=TICK_SIZE, loc="lower right")

    save_and_close(fig, output_path)


def chart_lambda_comparison(rows: list[dict[str, str]], output_path: Path) -> None:
    """Grouped bars: mean per-model bridging score at each λ column (with std across prompts)."""
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
            mean_val, std_val = mean_std(values)
            mean_values.append(mean_val)
            std_values.append(std_val)

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
    save_and_close(fig, output_path)
