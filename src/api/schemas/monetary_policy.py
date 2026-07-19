"""Monetary Policy API schemas, aligned with the Macro Pulse contract."""

from src.api.schemas.macro_pulse import (
    ChartCoverage,
    ChartInsight,
    ChartRecord,
    ChartSeriesMetadata,
    MacroPulseChart,
    MacroPulseKPI,
    MacroPulsePageMetadata,
    MacroPulseSummary,
)
from pydantic import BaseModel


class MonetaryPolicyPageMetadata(MacroPulsePageMetadata):
    pass


class MonetaryPolicySummary(MacroPulseSummary):
    pass


class MonetaryPolicyKPI(MacroPulseKPI):
    pass


class MonetaryPolicyChart(MacroPulseChart):
    pass


class MonetaryPolicyResponse(BaseModel):
    page: MonetaryPolicyPageMetadata
    summary: MonetaryPolicySummary
    kpis: list[MonetaryPolicyKPI]
    charts: list[MonetaryPolicyChart]


__all__ = [
    "ChartCoverage",
    "ChartInsight",
    "ChartRecord",
    "ChartSeriesMetadata",
    "MonetaryPolicyChart",
    "MonetaryPolicyKPI",
    "MonetaryPolicyPageMetadata",
    "MonetaryPolicyResponse",
    "MonetaryPolicySummary",
]
