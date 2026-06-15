from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.models import WaterQualityResult


class WaterQualityTestCreate(BaseModel):
    water_point_id: int
    sample_date: date
    report_no: str
    colony_count: Optional[float] = None
    total_coliform: Optional[float] = None
    heavy_metal: Optional[float] = None
    ph_value: Optional[float] = None
    other_indicators: Optional[str] = None
    result: WaterQualityResult
    remark: Optional[str] = None


class WaterQualityTestOut(BaseModel):
    id: int
    water_point_id: int
    tester_id: int
    sample_date: date
    report_no: str
    colony_count: Optional[float]
    total_coliform: Optional[float]
    heavy_metal: Optional[float]
    ph_value: Optional[float]
    other_indicators: Optional[str]
    result: WaterQualityResult
    remark: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
