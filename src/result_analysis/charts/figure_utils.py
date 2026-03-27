"""Figure layout, save, and footnote helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from result_analysis.charts import _backend  # noqa: F401
import matplotlib.pyplot as plt

from result_analysis.charts.style import DPI


def save_and_close(
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


def save_figure_with_footnote_below_x_axis(
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
