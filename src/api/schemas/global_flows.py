"""Currency, Commodities and Fixed Income API schemas."""

from pydantic import BaseModel

from src.api.schemas.macro_pulse import ChartCoverage, ChartInsight, ChartRecord, ChartSeriesMetadata


class GlobalFlowsPage(BaseModel):
    id: str
    title: str
    description: str


class GlobalFlowsSummary(BaseModel):
    headline: str
    body: str


class GlobalFlowsKPI(BaseModel):
    id: str
    metric: str
    name: str
    value: float | None
    delta: float | None = None
    description: str
    date: str | None
    main_unit: str
    delta_unit: str
    comparison_label: str | None = None
    delta_direction: str | None = None


class GlobalFlowsChart(BaseModel):
    id: str
    title: str
    description: str
    frequency: str
    chart_type: str
    series_metadata: list[ChartSeriesMetadata]
    records: list[ChartRecord]
    insight: ChartInsight | None = None
    coverage: ChartCoverage
    baseline_date: str | None = None
    zero_reference: float | None = None


class GlobalFlowsResponse(BaseModel):
    page: GlobalFlowsPage
    summary: GlobalFlowsSummary
    kpis: list[GlobalFlowsKPI]
    charts: list[GlobalFlowsChart]
