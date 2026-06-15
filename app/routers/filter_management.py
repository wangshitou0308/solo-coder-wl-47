from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import FilterRecord, FilterReplacement, WorkOrder, WorkOrderType, WorkOrderStatus, WaterPoint, User
from app.schemas.filter import FilterRecordCreate, FilterRecordUpdate, FilterRecordOut, FilterReplacementCreate, FilterReplacementOut
from app.utils.security import get_current_user
from app.utils.permissions import require_inspector_or_above, require_admin_or_supervisor, filter_by_area
import random
from datetime import datetime

router = APIRouter(prefix="/api/filters", tags=["滤芯管理"])


@router.post("/records", response_model=FilterRecordOut, status_code=status.HTTP_201_CREATED)
def create_filter_record(record_in: FilterRecordCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_supervisor)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == record_in.water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")

    capacity_based = (1 - record_in.cumulative_water_usage / record_in.rated_water_capacity) * 100
    time_based = (1 - record_in.cumulative_days / 365) * 100
    remaining_life_percent = max(0, min(capacity_based, time_based))

    record = FilterRecord(
        water_point_id=record_in.water_point_id,
        current_batch=record_in.current_batch,
        install_date=record_in.install_date,
        rated_water_capacity=record_in.rated_water_capacity,
        cumulative_days=record_in.cumulative_days,
        cumulative_water_usage=record_in.cumulative_water_usage,
        remaining_life_percent=round(remaining_life_percent, 2),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/records", response_model=list[FilterRecordOut])
def list_filter_records(db: Session = Depends(get_db), current_user: User = Depends(require_inspector_or_above)):
    query = db.query(FilterRecord).join(WaterPoint, FilterRecord.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    return query.all()


@router.get("/records/{record_id}", response_model=FilterRecordOut)
def get_filter_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_inspector_or_above)):
    record = db.query(FilterRecord).filter(FilterRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="滤芯记录不存在")
    return record


@router.put("/records/{record_id}", response_model=FilterRecordOut)
def update_filter_record(record_id: int, record_in: FilterRecordUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_supervisor)):
    record = db.query(FilterRecord).filter(FilterRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="滤芯记录不存在")

    if record_in.cumulative_days is not None:
        record.cumulative_days = record_in.cumulative_days
    if record_in.cumulative_water_usage is not None:
        record.cumulative_water_usage = record_in.cumulative_water_usage

    capacity_based = (1 - record.cumulative_water_usage / record.rated_water_capacity) * 100
    time_based = (1 - record.cumulative_days / 365) * 100
    record.remaining_life_percent = round(max(0, min(capacity_based, time_based)), 2)

    db.commit()
    db.refresh(record)
    return record


@router.get("/expiry-warning", response_model=list[FilterRecordOut])
def get_expiry_warning(db: Session = Depends(get_db), current_user: User = Depends(require_inspector_or_above)):
    query = db.query(FilterRecord).join(WaterPoint, FilterRecord.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    query = query.filter(FilterRecord.remaining_life_percent < 30)
    query = query.order_by(FilterRecord.remaining_life_percent.asc())
    return query.all()


@router.post("/replacements", response_model=FilterReplacementOut, status_code=status.HTTP_201_CREATED)
def create_filter_replacement(replacement_in: FilterReplacementCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_supervisor)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == replacement_in.water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")

    filter_record = db.query(FilterRecord).filter(FilterRecord.water_point_id == replacement_in.water_point_id).first()
    was_below_threshold = False
    if filter_record:
        was_below_threshold = filter_record.remaining_life_percent < 30

    replacement = FilterReplacement(
        water_point_id=replacement_in.water_point_id,
        old_batch=replacement_in.old_batch,
        new_batch=replacement_in.new_batch,
        replacement_date=replacement_in.replacement_date,
        replaced_by=replacement_in.replaced_by,
        replaced_by_id=current_user.id,
        remark=replacement_in.remark,
    )
    db.add(replacement)

    if filter_record:
        filter_record.current_batch = replacement_in.new_batch
        filter_record.cumulative_days = 0
        filter_record.cumulative_water_usage = 0.0
        filter_record.remaining_life_percent = 100.0
        filter_record.last_replacement_date = replacement_in.replacement_date

    if was_below_threshold:
        order_no = f"WO{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        work_order = WorkOrder(
            order_no=order_no,
            water_point_id=replacement_in.water_point_id,
            order_type=WorkOrderType.FILTER_REPLACEMENT,
            status=WorkOrderStatus.PENDING,
            description=f"滤芯更换：{replacement_in.old_batch} -> {replacement_in.new_batch}",
            created_by=current_user.id,
        )
        db.add(work_order)

    db.commit()
    db.refresh(replacement)
    return replacement


@router.get("/replacements", response_model=list[FilterReplacementOut])
def list_filter_replacements(db: Session = Depends(get_db), current_user: User = Depends(require_inspector_or_above)):
    query = db.query(FilterReplacement).join(WaterPoint, FilterReplacement.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    return query.all()


@router.get("/replacements/water-point/{wp_id}", response_model=list[FilterReplacementOut])
def list_replacements_by_water_point(wp_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_inspector_or_above)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == wp_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")

    query = db.query(FilterReplacement).join(WaterPoint, FilterReplacement.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    query = query.filter(FilterReplacement.water_point_id == wp_id)
    query = query.order_by(FilterReplacement.replacement_date.desc())
    return query.all()
