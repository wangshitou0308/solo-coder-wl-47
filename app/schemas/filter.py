from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class FilterRecordCreate(BaseModel):
    water_point_id: int
    current_batch: str
    install_date: date
    rated_water_capacity: float
    cumulative_days: int = 0
    cumulative_water_usage: float = 0.0


class FilterRecordUpdate(BaseModel):
    cumulative_days: Optional[int] = None
    cumulative_water_usage: Optional[float] = None


class FilterRecordOut(BaseModel):
    id: int
    water_point_id: int
    current_batch: str
    install_date: date
    rated_water_capacity: float
    cumulative_days: int
    cumulative_water_usage: float
    remaining_life_percent: float
    last_replacement_date: Optional[date]
    created_at: datetime

    model_config = {"from_attributes": True}


class FilterReplacementCreate(BaseModel):
    water_point_id: int
    old_batch: str
    new_batch: str
    replacement_date: date
    replaced_by: str
    remark: Optional[str] = None


class FilterReplacementOut(BaseModel):
    id: int
    water_point_id: int
    old_batch: str
    new_batch: str
    replacement_date: date
    replaced_by: str
    replaced_by_id: int
    remark: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
