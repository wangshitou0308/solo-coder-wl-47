from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import CitizenReport, FaultType, WorkOrder, WorkOrderType, WorkOrderStatus, WaterPoint, User
from app.schemas.citizen_report import CitizenReportCreate, CitizenReportFeedback, CitizenReportOut
from app.utils.security import get_current_user
from app.utils.permissions import require_admin_or_supervisor, filter_by_area
import random, math
from datetime import datetime

router = APIRouter(prefix="/api/citizen-reports", tags=["市民上报"])


def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.cos(lat1_r) * math.cos(lat2_r) * math.cos(dlng) + math.sin(lat1_r) * math.sin(lat2_r)
    a = max(min(a, 1.0), -1.0)
    return R * math.acos(a)


def find_nearest_water_point(db: Session, latitude: float, longitude: float):
    water_points = db.query(WaterPoint).all()
    nearest = None
    min_distance = float("inf")
    for wp in water_points:
        dist = haversine(latitude, longitude, wp.latitude, wp.longitude)
        if dist < min_distance:
            min_distance = dist
            nearest = wp
    if nearest and min_distance <= 1.0:
        return nearest, min_distance
    return None, None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_citizen_report(report_in: CitizenReportCreate, db: Session = Depends(get_db)):
    water_point = None
    distance = None
    if report_in.latitude is not None and report_in.longitude is not None:
        water_point, distance = find_nearest_water_point(db, report_in.latitude, report_in.longitude)

    if not water_point:
        report = CitizenReport(
            water_point_id=None,
            reporter_name=report_in.reporter_name,
            reporter_phone=report_in.reporter_phone,
            fault_type=report_in.fault_type,
            description=report_in.description,
            longitude=report_in.longitude,
            latitude=report_in.latitude,
            is_resolved=False,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return {
            "report": CitizenReportOut.model_validate(report),
            "message": "未找到1公里范围内的饮水点，上报已记录但未关联饮水点",
        }

    report = CitizenReport(
        water_point_id=water_point.id,
        reporter_name=report_in.reporter_name,
        reporter_phone=report_in.reporter_phone,
        fault_type=report_in.fault_type,
        description=report_in.description,
        longitude=report_in.longitude,
        latitude=report_in.latitude,
        is_resolved=False,
    )
    db.add(report)
    db.flush()

    order_no = "WO" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
    work_order = WorkOrder(
        order_no=order_no,
        water_point_id=water_point.id,
        order_type=WorkOrderType.COMPLAINT,
        status=WorkOrderStatus.PENDING,
        description=f"市民上报故障：{report_in.fault_type.value}" + (f"，{report_in.description}" if report_in.description else ""),
    )
    db.add(work_order)
    db.flush()

    report.work_order_id = work_order.id
    db.commit()
    db.refresh(report)

    return {
        "report": CitizenReportOut.model_validate(report),
        "message": "上报成功，已自动关联最近饮水点并创建工单",
    }


@router.get("", response_model=list[CitizenReportOut])
def list_citizen_reports(
    water_point_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(CitizenReport).join(WaterPoint, CitizenReport.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    if water_point_id is not None:
        query = query.filter(CitizenReport.water_point_id == water_point_id)
    query = query.order_by(CitizenReport.created_at.desc())
    return query.all()


@router.get("/{report_id}", response_model=CitizenReportOut)
def get_citizen_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = (
        db.query(CitizenReport)
        .join(WaterPoint, CitizenReport.water_point_id == WaterPoint.id)
        .filter(CitizenReport.id == report_id)
    )
    report = filter_by_area(report, current_user, WaterPoint.area).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上报记录不存在")
    return report


@router.put("/{report_id}/feedback", response_model=CitizenReportOut)
def feedback_citizen_report(
    report_id: int,
    feedback_in: CitizenReportFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_supervisor),
):
    report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="上报记录不存在")
    report.feedback = feedback_in.feedback
    report.is_resolved = True
    db.commit()
    db.refresh(report)
    return report
