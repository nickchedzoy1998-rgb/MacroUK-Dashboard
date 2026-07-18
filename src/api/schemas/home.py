from datetime import date

from pydantic import BaseModel


class HomeKPI(BaseModel):
    kpi_id: str
    metric_id: str
    name: str
    value: float
    delta: float | None = None
    date: date
    comparison_type: str
    comparison_label: str | None = None
    main_unit: str | None = None
    delta_unit: str | None = None
    delta_direction: str | None = None
    description: str

    model_config = {"from_attributes": True}


class HomeSummaryNarrative(BaseModel):
    headline: str
    body: str


class HomeHighlight(BaseModel):
    kpi_id: str
    title: str
    text: str
    importance: int
    direction: str


class HomeSummaryResponse(BaseModel):
    kpis: list[HomeKPI]
    summary: HomeSummaryNarrative
    highlights: list[HomeHighlight]
