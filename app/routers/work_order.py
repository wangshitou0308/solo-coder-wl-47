import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    WorkOrder,
    WorkOrderType,
    WorkOrderStatus,
    WaterPoint,
    WaterPointStatus,
    User,
    UserRole,
    CitizenReport,
)
from app.schemas.work_order import WorkOrderCreate, WorkOrderAssign, WorkOrderComplete, WorkOrderOut
from app.utils.security import get_current_user
from app.utils.permissions import require_admin_or_supervisor, filter_by_area

router = APIRouter(prefix="/api/work-orders", tags=["工单管理"])


@router.post("", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED)
def create_work_order(
    work_order_in: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == work_order_in.water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="直饮水点不存在")

    order_no = "WO" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))

    work_order = WorkOrder(
        order_no=order_no,
        water_point_id=work_order_in.water_point_id,
        order_type=work_order_in.order_type,
        description=work_order_in.description,
        assigned_to=work_order_in.assigned_to,
        created_by=current_user.id,
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


@router.get("", response_model=list[WorkOrderOut])
def list_work_orders(
    status_filter: WorkOrderStatus = Query(default=None, alias="status"),
    order_type: WorkOrderType = Query(default=None, alias="order_type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WorkOrder).join(WaterPoint, WorkOrder.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)

    if status_filter:
        query = query.filter(WorkOrder.status == status_filter)
    if order_type:
        query = query.filter(WorkOrder.order_type == order_type)

    return query.all()


@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")
    return work_order


@router.put("/{work_order_id}/assign", response_model=WorkOrderOut)
def assign_work_order(
    work_order_id: int,
    assign_in: WorkOrderAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")

    assignee = db.query(User).filter(User.id == assign_in.assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="被指派用户不存在")

    work_order.assigned_to = assign_in.assigned_to
    work_order.status = WorkOrderStatus.ASSIGNED
    db.commit()
    db.refresh(work_order)
    return work_order


@router.put("/{work_order_id}/start", response_model=WorkOrderOut)
def start_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")

    is_assigned_user = work_order.assigned_to == current_user.id
    is_admin_or_supervisor = current_user.role in (UserRole.ADMIN, UserRole.MAINTENANCE_SUPERVISOR)
    if not is_assigned_user and not is_admin_or_supervisor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有被指派人员或管理员/运维主管可以开始工单")

    work_order.status = WorkOrderStatus.IN_PROGRESS
    db.commit()
    db.refresh(work_order)
    return work_order


@router.put("/{work_order_id}/complete", response_model=WorkOrderOut)
def complete_work_order(
    work_order_id: int,
    complete_in: WorkOrderComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")

    is_assigned_user = work_order.assigned_to == current_user.id
    is_admin_or_supervisor = current_user.role in (UserRole.ADMIN, UserRole.MAINTENANCE_SUPERVISOR)
    if not is_assigned_user and not is_admin_or_supervisor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有被指派人员或管理员/运维主管可以完成工单")

    work_order.status = WorkOrderStatus.COMPLETED
    work_order.completed_at = datetime.utcnow()
    work_order.feedback = complete_in.feedback

    if work_order.order_type in (WorkOrderType.EMERGENCY, WorkOrderType.REPAIR):
        water_point = db.query(WaterPoint).filter(WaterPoint.id == work_order.water_point_id).first()
        if water_point and water_point.status == WaterPointStatus.DISABLED:
            water_point.status = WaterPointStatus.ONLINE

    if work_order.order_type == WorkOrderType.COMPLAINT:
        citizen_report = db.query(CitizenReport).filter(CitizenReport.work_order_id == work_order.id).first()
        if citizen_report and not citizen_report.is_resolved:
            citizen_report.is_resolved = True
            if complete_in.feedback and not citizen_report.feedback:
                citizen_report.feedback = complete_in.feedback

    db.commit()
    db.refresh(work_order)
    return work_order


@router.put("/{work_order_id}/close", response_model=WorkOrderOut)
def close_work_order(
    work_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="工单不存在")

    work_order.status = WorkOrderStatus.CLOSED

    if work_order.order_type == WorkOrderType.COMPLAINT:
        citizen_report = db.query(CitizenReport).filter(CitizenReport.work_order_id == work_order.id).first()
        if citizen_report and not citizen_report.is_resolved:
            citizen_report.is_resolved = True

    db.commit()
    db.refresh(work_order)
    return work_order
