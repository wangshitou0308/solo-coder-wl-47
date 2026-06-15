from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Inspection, InspectionResult, WorkOrder, WorkOrderType, WorkOrderStatus, WaterPoint, User
from app.schemas.inspection import InspectionCreate, InspectionOut
from app.utils.security import get_current_user
from app.utils.permissions import require_inspector_or_above, filter_by_area
import random
from datetime import datetime

router = APIRouter(prefix="/api/inspections", tags=["巡检管理"])


@router.post("", response_model=InspectionOut, status_code=status.HTTP_201_CREATED)
def create_inspection(inspection_in: InspectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_inspector_or_above)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == inspection_in.water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")

    failed_items = []
    if not inspection_in.appearance_ok:
        failed_items.append("外观异常")
    if not inspection_in.water_output_ok:
        failed_items.append("出水异常")
    if not inspection_in.button_sensitivity_ok:
        failed_items.append("按键灵敏度异常")
    if not inspection_in.drainage_ok:
        failed_items.append("排水异常")
    if inspection_in.tds_value > inspection_in.tds_threshold:
        failed_items.append(f"TDS值超标({inspection_in.tds_value}>{inspection_in.tds_threshold})")

    result = InspectionResult.ABNORMAL if failed_items else InspectionResult.NORMAL

    inspection = Inspection(
        water_point_id=inspection_in.water_point_id,
        inspector_id=current_user.id,
        inspection_date=inspection_in.inspection_date,
        appearance_ok=inspection_in.appearance_ok,
        water_output_ok=inspection_in.water_output_ok,
        button_sensitivity_ok=inspection_in.button_sensitivity_ok,
        drainage_ok=inspection_in.drainage_ok,
        tds_value=inspection_in.tds_value,
        tds_threshold=inspection_in.tds_threshold,
        result=result,
        remark=inspection_in.remark,
    )
    db.add(inspection)
    db.flush()

    if result == InspectionResult.ABNORMAL:
        order_no = "WO" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
        description = "巡检异常，以下项目不合格：" + "、".join(failed_items)
        work_order = WorkOrder(
            order_no=order_no,
            water_point_id=inspection_in.water_point_id,
            order_type=WorkOrderType.REPAIR,
            status=WorkOrderStatus.PENDING,
            description=description,
            created_by=current_user.id,
        )
        db.add(work_order)

    db.commit()
    db.refresh(inspection)
    return inspection


@router.get("", response_model=list[InspectionOut])
def list_inspections(water_point_id: int = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Inspection).join(WaterPoint, Inspection.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    if water_point_id is not None:
        query = query.filter(Inspection.water_point_id == water_point_id)
    query = query.order_by(Inspection.created_at.desc())
    return query.all()


@router.get("/{inspection_id}", response_model=InspectionOut)
def get_inspection(inspection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inspection = db.query(Inspection).join(WaterPoint, Inspection.water_point_id == WaterPoint.id).filter(Inspection.id == inspection_id)
    inspection = filter_by_area(inspection, current_user, WaterPoint.area).first()
    if not inspection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="巡检记录不存在")
    return inspection


@router.get("/water-point/{wp_id}", response_model=list[InspectionOut])
def list_inspections_by_water_point(wp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == wp_id)
    water_point = filter_by_area(water_point, current_user, WaterPoint.area).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")
    inspections = db.query(Inspection).filter(Inspection.water_point_id == wp_id).order_by(Inspection.created_at.desc()).all()
    return inspections
