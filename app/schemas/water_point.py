from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.models.models import WaterPointStatus


class WaterPointCreate(BaseModel):
    equipment_no: str
    name: str
    area: str
    address: str
    longitude: float
    latitude: float
    model: str
    install_date: date
    filter_spec: str
    rated_water_capacity: float


class WaterPointUpdate(BaseModel):
    name: Optional[str] = None
    area: Optional[str] = None
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    model: Optional[str] = None
    filter_spec: Optional[str] = None
    rated_water_capacity: Optional[float] = None
    status: Optional[WaterPointStatus] = None


class WaterPointOut(BaseModel):
    id: int
    equipment_no: str
    name: str
    area: str
    address: str
    longitude: float
    latitude: float
    model: str
    install_date: date
    filter_spec: str
    rated_water_capacity: float
    status: WaterPointStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class WaterPointAreaGroup(BaseModel):
    area: str
    count: int
