from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.models import InspectionResult


class InspectionCreate(BaseModel):
    water_point_id: int
    inspection_date: date
    appearance_ok: bool
    water_output_ok: bool
    button_sensitivity_ok: bool
    drainage_ok: bool
    tds_value: float
    tds_threshold: float = 50.0
    remark: Optional[str] = None


class InspectionOut(BaseModel):
    id: int
    water_point_id: int
    inspector_id: int
    inspection_date: date
    appearance_ok: bool
    water_output_ok: bool
    button_sensitivity_ok: bool
    drainage_ok: bool
    tds_value: float
    tds_threshold: float
    result: InspectionResult
    remark: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
