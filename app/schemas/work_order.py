from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.models import WorkOrderType, WorkOrderStatus


class WorkOrderCreate(BaseModel):
    water_point_id: int
    order_type: WorkOrderType
    description: str
    assigned_to: Optional[int] = None


class WorkOrderAssign(BaseModel):
    assigned_to: int


class WorkOrderComplete(BaseModel):
    feedback: Optional[str] = None


class WorkOrderOut(BaseModel):
    id: int
    order_no: str
    water_point_id: int
    order_type: WorkOrderType
    status: WorkOrderStatus
    description: str
    assigned_to: Optional[int]
    created_by: Optional[int]
    completed_at: Optional[datetime]
    feedback: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
