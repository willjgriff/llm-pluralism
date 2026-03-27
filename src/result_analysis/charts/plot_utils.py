"""Plotting helpers shared across chart modules."""

from __future__ import annotations

from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

from result_analysis.charts.figure_utils import save_and_close
from result_analysis.charts.style import ANNOTATION_SIZE, LABEL_SIZE, TICK_SIZE, TITLE_SIZE


def mean_std(values: list[float]) -> tuple[float, float]:
    """Return population mean and standard deviation of ``values``."""
    arr = np.array(values, dtype=float)
    return float(arr.mean()), float(arr.std(ddof=0))


def color_by_model(models: list[str]) -> dict[str, tuple[float, float, float, float]]:
    """Map each model label to a distinct colour from tab10."""
    cmap = plt.get_cmap("tab10")
    return {model: cmap(i % 10) for i, model in enumerate(models)}


def annotate_heatmap_cells(ax: plt.Axes, matrix: np.ndarray, *, decimals: int = 2) -> None:
    """Draw text in each heatmap cell using ``decimals`` places after the decimal point."""
    fmt = f"{{:.{decimals}f}}"
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                fmt.format(matrix[i, j]),
                ha="center",
                va="center",
                color="black",
                fontsize=ANNOTATION_SIZE,
            )


def save_bar_chart_with_error_bars(
    *,
    categories: list[str],
    means: list[float],
    stds: list[float],
    color: str,
    title: str,
    ylabel: str,
    x_rotation: float,
    output_path: Path,
    figsize: tuple[float, float] = (10, 5),
) -> None:
    """Create a vertical bar chart with one bar per category and y-error bars, then save."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(categories, means, yerr=stds, capsize=4, color=color)
    ax.set_title(title, fontsize=TITLE_SIZE)
    ax.set_ylabel(ylabel, fontsize=LABEL_SIZE)
    ax.tick_params(axis="x", labelrotation=x_rotation, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelsize=TICK_SIZE)
    save_and_close(fig, output_path)


def save_heatmap_with_colorbar(
    *,
    matrix: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
    norm: colors.TwoSlopeNorm,
    title: str,
    xlabel: str | None,
    ylabel: str | None,
    output_path: Path,
    figsize: tuple[float, float],
    aspect: str,
    x_tick_rotation: int,
    y_tick_rotation: int = 0,
    annotate_decimals: int = 2,
) -> None:
    """Render a coolwarm heatmap with annotations, colorbar, and save to ``output_path``."""
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(matrix, cmap="coolwarm", norm=norm, aspect=aspect)
    ax.set_title(title, fontsize=TITLE_SIZE)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=LABEL_SIZE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=LABEL_SIZE)
    ax.set_xticks(np.arange(len(col_labels)), labels=col_labels)
    ax.set_yticks(np.arange(len(row_labels)), labels=row_labels)
    ax.tick_params(axis="x", labelrotation=x_tick_rotation, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", labelrotation=y_tick_rotation, labelsize=TICK_SIZE)
    annotate_heatmap_cells(ax, matrix, decimals=annotate_decimals)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    save_and_close(fig, output_path)


def response_model_column(row: dict[str, str]) -> str:
    """Return ``response_model`` if set, else ``source_model``, stripped."""
    return (row.get("response_model") or row["source_model"]).strip()
