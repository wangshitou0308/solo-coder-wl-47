from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.models import FaultType


class CitizenReportCreate(BaseModel):
    reporter_name: Optional[str] = None
    reporter_phone: Optional[str] = None
    fault_type: FaultType
    description: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class CitizenReportFeedback(BaseModel):
    feedback: str


class CitizenReportOut(BaseModel):
    id: int
    water_point_id: Optional[int]
    reporter_name: Optional[str]
    reporter_phone: Optional[str]
    fault_type: FaultType
    description: Optional[str]
    longitude: Optional[float]
    latitude: Optional[float]
    work_order_id: Optional[int]
    is_resolved: bool
    feedback: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
