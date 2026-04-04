"""Analysis chart generation (PNG outputs under ``output/analysis``)."""

from __future__ import annotations

from result_analysis.charts import _backend  # noqa: F401
from result_analysis.charts.pipeline import generate_analysis_charts

__all__ = ["generate_analysis_charts"]
