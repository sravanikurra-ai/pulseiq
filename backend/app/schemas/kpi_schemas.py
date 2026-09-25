from datetime import date
from pydantic import BaseModel


class KPIValue(BaseModel):
    kpi_name: str
    period_start: date
    period_end: date
    value: float
    dimension: str | None = None
    note: str | None = None  # used to surface honest limitations, e.g. on conversion_rate