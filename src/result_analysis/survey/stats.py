"""Thin wrapper around scipy stats used by survey charts."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import pearsonr


def pearson_r_with_p(
    x_values: np.ndarray, y_values: np.ndarray, *, min_pairs: int = 5
) -> tuple[float, float]:
    """Return ``(r, p)`` Pearson correlation, or ``(nan, nan)`` when ill-defined.

    Parameters:
        x_values: First numeric series.
        y_values: Second numeric series (same length as ``x_values``).
        min_pairs: Minimum number of paired observations required before
            attempting the correlation. Returns NaN if not met.

    Returns:
        Tuple of correlation coefficient and two-sided p-value. NaN values are
        returned when the inputs are too short or either series has zero
        variance.
    """
    if len(x_values) < min_pairs:
        return math.nan, math.nan
    if np.std(x_values) == 0 or np.std(y_values) == 0:
        return math.nan, math.nan
    result = pearsonr(x_values, y_values)
    return float(result[0]), float(result[1])
