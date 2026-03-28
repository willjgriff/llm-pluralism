"""Charts derived from bridging score CSV rows."""

from __future__ import annotations

from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.colors import to_hex

from result_analysis.charts.figure_utils import save_and_close
from result_analysis.charts.plot_utils import (
    color_by_model,
    mean_std,
    save_bar_chart_with_error_bars,
    save_heatmap_with_colorbar,
)
from result_analysis.charts.style import LABEL_SIZE, TICK_SIZE, TITLE_SIZE
from result_analysis.scoring.bridging_score import LAMBDA_VALUES

# Half-width of uniform jitter on mean_score and std_score (matplotlib + Plotly scatter).
_MEAN_STD_SCATTER_JITTER = 0.04
_MEAN_STD_SCATTER_JITTER_SEED = 42


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
    """Heatmap: mean bridging score per model × topic group across all prompts in that cell."""
    models = sorted({row["response_model"] for row in rows})
    groups = sorted({row["group_name"] for row in rows})
    bridging_scores_by_model_and_group: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        cell_key = (row["response_model"], row["group_name"])
        bridging_scores_by_model_and_group.setdefault(cell_key, []).append(
            float(row["bridging_score"])
        )

    matrix = np.array(
        [
            [
                float(np.mean(bridging_scores_by_model_and_group[(model, group)]))
                if (model, group) in bridging_scores_by_model_and_group
                else float("nan")
                for group in groups
            ]
            for model in models
        ],
        dtype=float,
    )
    vmin = float(np.nanmin(matrix))
    vmax = float(np.nanmax(matrix))
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
    """Scatter: ``mean_score`` vs ``std_score`` per response, coloured by model.

    Applies small uniform jitter to x/y and uses alpha 0.7 to reduce overplotting.
    """
    models = sorted({row["response_model"] for row in rows})
    colors_map = color_by_model(models)
    rng = np.random.default_rng(_MEAN_STD_SCATTER_JITTER_SEED)
    jitter = _MEAN_STD_SCATTER_JITTER

    fig, ax = plt.subplots(figsize=(10, 6))
    for model in models:
        model_rows = [row for row in rows if row["response_model"] == model]
        n = len(model_rows)
        x_vals = np.array([float(row["mean_score"]) for row in model_rows], dtype=float)
        y_vals = np.array([float(row["std_score"]) for row in model_rows], dtype=float)
        x_vals = x_vals + rng.uniform(-jitter, jitter, size=n)
        y_vals = y_vals + rng.uniform(-jitter, jitter, size=n)
        ax.scatter(
            x_vals,
            y_vals,
            label=model,
            color=colors_map[model],
            alpha=0.7,
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


def chart_mean_vs_std_scatter_interactive(rows: list[dict[str, str]], output_path: Path) -> None:
    """Standalone HTML scatter: same data as ``chart_mean_vs_std_scatter`` with rich hover text.

    Uses the same jitter seed and half-width as the matplotlib chart. Hover shows
    untruncated prompt and numeric fields from the CSV (not jittered coordinates).

    Parameters:
        rows: Bridging score table rows (``response_model``, ``mean_score``, ``std_score``, etc.).
        output_path: Path for ``mean_vs_std_scatter.html`` (``include_plotlyjs=True``).

    Returns:
        Nothing; writes ``output_path``.
    """
    import plotly.graph_objects as go

    models = sorted({row["response_model"] for row in rows})
    colors_map = color_by_model(models)
    rng = np.random.default_rng(_MEAN_STD_SCATTER_JITTER_SEED)
    jitter = _MEAN_STD_SCATTER_JITTER

    fig = go.Figure()
    for model in models:
        model_rows = [row for row in rows if row["response_model"] == model]
        n = len(model_rows)
        x_raw = np.array([float(row["mean_score"]) for row in model_rows], dtype=float)
        y_raw = np.array([float(row["std_score"]) for row in model_rows], dtype=float)
        x_j = x_raw + rng.uniform(-jitter, jitter, size=n)
        y_j = y_raw + rng.uniform(-jitter, jitter, size=n)
        hex_color = to_hex(colors_map[model], keep_alpha=False)
        customdata = np.column_stack(
            [
                [row["prompt"] for row in model_rows],
                [row["question_id"] for row in model_rows],
                x_raw,
                y_raw,
                [float(row["bridging_score"]) for row in model_rows],
            ]
        )
        fig.add_trace(
            go.Scatter(
                x=x_j,
                y=y_j,
                mode="markers",
                name=model,
                marker=dict(
                    color=hex_color,
                    size=9,
                    opacity=0.7,
                    line=dict(color="white", width=0.5),
                ),
                customdata=customdata,
                hovertemplate=(
                    "<b>Model name</b>: %{fullData.name}<br>"
                    "<b>Prompt text</b>: %{customdata[0]}<br>"
                    "<b>Question ID</b>: %{customdata[1]}<br>"
                    "<b>Mean score</b>: %{customdata[2]:.6f}<br>"
                    "<b>Std deviation</b>: %{customdata[3]:.6f}<br>"
                    "<b>Bridging score</b>: %{customdata[4]:.6f}<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Mean vs Std Dev of Persona Scores by Response (Interactive)",
        xaxis_title="Mean Score",
        yaxis_title="Score Std Deviation",
        template="plotly_white",
        legend=dict(font=dict(size=TICK_SIZE)),
        title_font_size=TITLE_SIZE,
    )
    fig.update_xaxes(tickfont=dict(size=TICK_SIZE))
    fig.update_yaxes(tickfont=dict(size=TICK_SIZE))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)


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
