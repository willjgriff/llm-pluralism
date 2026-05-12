"""Build the 'what transfers' summary table from chart-derived statistics."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from result_analysis.survey.constants import AXIS_PAIRS, PERSONA_ORDER

_HUMAN_OPPOSE_STRONG = -0.3
_HUMAN_OPPOSE_WEAK = -0.05
_DIAGONAL_AGREE = 0.2

SUMMARY_CSV_FILENAME = "what_transfers_summary.csv"
SUMMARY_MARKDOWN_FILENAME = "what_transfers_summary.md"


def classify_axis(human_r: float, diagonal_r: float, sample_size: int) -> str:
    """Heuristically classify how well an axis transfers from AI to humans.

    Parameters:
        human_r: Pearson correlation between the axis's two personas as rated
            by humans (negative means humans disagree as expected).
        diagonal_r: Mean of same-persona Pearson correlations along the
            agreement-matrix diagonal for this axis.
        sample_size: Total diagonal sample count contributing to
            ``diagonal_r``; used to flag axes as ``Untested`` when zero.

    Returns:
        One of ``"Validates"``, ``"Partial"``, ``"Fails"``, or ``"Untested"``.
    """
    if math.isnan(human_r) or sample_size == 0:
        return "Untested"
    if human_r < _HUMAN_OPPOSE_STRONG and diagonal_r > _DIAGONAL_AGREE:
        return "Validates"
    if human_r < _HUMAN_OPPOSE_WEAK or diagonal_r > _DIAGONAL_AGREE:
        return "Partial"
    return "Fails"


def _format_signed(value: float) -> str:
    """Format a value with a sign and two decimal places, or ``n/a`` if NaN.

    Parameters:
        value: Numeric value possibly NaN.

    Returns:
        Either ``"+0.42"`` style string or ``"n/a"``.
    """
    return f"{value:+.2f}" if not math.isnan(value) else "n/a"


def _diagonal_stats_for_axis(
    persona_a: str,
    persona_b: str,
    agreement_matrix: np.ndarray,
    sample_counts: np.ndarray,
    human_personas: list[str],
) -> tuple[float, int]:
    """Return mean diagonal r and total sample count for an axis's two personas.

    Parameters:
        persona_a: First persona name on the axis.
        persona_b: Second persona name on the axis.
        agreement_matrix: Output of
            :func:`chart_human_ai_agreement_matrix`.
        sample_counts: Sibling sample-count matrix.
        human_personas: Row labels for ``agreement_matrix``.

    Returns:
        Tuple ``(mean_diagonal_r, total_sample_count)``. Mean is NaN if no
        diagonal entries are available for the axis.
    """
    diagonal_correlations: list[float] = []
    diagonal_counts: list[int] = []
    for persona_name in (persona_a, persona_b):
        if persona_name not in human_personas or persona_name not in PERSONA_ORDER:
            continue
        row_index = human_personas.index(persona_name)
        column_index = PERSONA_ORDER.index(persona_name)
        correlation = agreement_matrix[row_index, column_index]
        if not math.isnan(correlation):
            diagonal_correlations.append(float(correlation))
            diagonal_counts.append(int(sample_counts[row_index, column_index]))
    if not diagonal_correlations:
        return math.nan, 0
    return float(np.mean(diagonal_correlations)), int(sum(diagonal_counts))


def build_summary_table(
    pair_correlations: pd.DataFrame,
    agreement_matrix: np.ndarray,
    sample_counts: np.ndarray,
    human_personas: list[str],
) -> pd.DataFrame:
    """Combine pair and diagonal statistics into a one-row-per-axis summary.

    Parameters:
        pair_correlations: Output of
            :func:`compute_persona_pair_correlations` (one row per axis).
        agreement_matrix: Human-vs-AI agreement matrix from
            :func:`chart_human_ai_agreement_matrix`.
        sample_counts: Sample count matrix paired with ``agreement_matrix``.
        human_personas: Row labels for those matrices.

    Returns:
        Display-ready DataFrame with columns ``Axis``, ``Pair``,
        ``AI pair r``, ``Human pair r``, ``Diagonal agreement r (mean)``,
        ``Verdict``.
    """
    rows: list[dict[str, str]] = []
    for axis_name, persona_a, persona_b in AXIS_PAIRS:
        pair_row = pair_correlations[pair_correlations["axis"] == axis_name].iloc[0]
        diagonal_r, total_diagonal_n = _diagonal_stats_for_axis(
            persona_a, persona_b, agreement_matrix, sample_counts, human_personas
        )
        verdict = classify_axis(pair_row["human_r"], diagonal_r, total_diagonal_n)

        human_pair_label = (
            f"{_format_signed(pair_row['human_r'])} (N={int(pair_row['human_n'])})"
        )
        diagonal_label = (
            f"{_format_signed(diagonal_r)} (N={total_diagonal_n})"
            if not math.isnan(diagonal_r)
            else "n/a"
        )
        rows.append(
            {
                "Axis": axis_name,
                "Pair": pair_row["pair"],
                "AI pair r": _format_signed(pair_row["ai_r"]),
                "Human pair r": human_pair_label,
                "Diagonal agreement r (mean)": diagonal_label,
                "Verdict": verdict,
            }
        )
    return pd.DataFrame(rows)


def write_summary_table(summary_table: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    """Write the summary table as CSV and Markdown into ``output_dir``.

    Parameters:
        summary_table: Output of :func:`build_summary_table`.
        output_dir: Destination directory; assumed to exist.

    Returns:
        Tuple of ``(csv_path, markdown_path)`` for the written files.
    """
    csv_path = output_dir / SUMMARY_CSV_FILENAME
    markdown_path = output_dir / SUMMARY_MARKDOWN_FILENAME
    summary_table.to_csv(csv_path, index=False)
    markdown_path.write_text(summary_table.to_markdown(index=False))
    return csv_path, markdown_path
