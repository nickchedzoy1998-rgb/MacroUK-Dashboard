"""Validated response models for the Macro Pulse API."""

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, create_model

from src.utilities.config_loader import load_config


class MacroPulsePageMetadata(BaseModel):
    id: str
    title: str
    description: str


class MacroPulseSummary(BaseModel):
    headline: str
    body: str


class MacroPulseKPI(BaseModel):
    id: str
    metric: str
    name: str
    value: float | None
    delta: float | None = None
    description: str
    date: date | None
    main_unit: str
    delta_unit: str
    comparison_label: str | None = None
    delta_direction: str | None = None


class ChartSeriesMetadata(BaseModel):
    metric: str
    label: str
    unit: str
    role: str
    axis: str
    display_order: int
    optional: bool = False


class ChartRecord(BaseModel):
    """One prepared observation with values keyed by metric identifier."""

    date: date
    values: dict[str, float | None]


class ChartCoverage(BaseModel):
    requested_metrics: list[str]
    available_metrics: list[str]
    missing_metrics: list[str]
    first_observation: dict[str, date | None]
    latest_observation: dict[str, date | None]
    valid_observations: dict[str, int]


class ChartInsight(BaseModel):
    chart_id: str
    headline: str
    body: str
    direction: str
    as_of_date: date


class MacroPulseChart(BaseModel):
    id: str
    title: str
    description: str
    frequency: str
    chart_type: str
    series_metadata: list[ChartSeriesMetadata]
    records: list[ChartRecord]
    insight: ChartInsight | None = None
    coverage: ChartCoverage
    target: float | None = None
    zero_reference: float | None = None


class MacroPulseResponse(BaseModel):
    page: MacroPulsePageMetadata
    summary: MacroPulseSummary
    kpis: list[MacroPulseKPI]
    charts: list[MacroPulseChart]


# Compatibility schemas for the existing per-chart routes.
macropulse_config = load_config("charts", "MacroPulse")


def macro_pulse_schema() -> dict[str, type[BaseModel]]:
    chart_schemas: dict[str, type[BaseModel]] = {}
    for chart, config in macropulse_config.items():
        fields: dict[str, Any] = {
            "date": (date, ...),
            "chart": (str, ...),
        }
        for metric in (*config.get("metrics", []), *config.get("optional_metrics", [])):
            fields[metric] = (float | None, None)
        dynamic_model = create_model(
            f"{chart}Row",
            __base__=BaseModel,
            **fields,
        )
        dynamic_model.model_config = ConfigDict(from_attributes=True)
        chart_schemas[chart] = dynamic_model
    return chart_schemas


CHART_SCHEMAS = macro_pulse_schema()
