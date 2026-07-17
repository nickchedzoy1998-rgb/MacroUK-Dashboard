from pydantic import BaseModel
from datetime import date


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


class HomeSummaryResponse(BaseModel):
    kpis: list[HomeKPI]
