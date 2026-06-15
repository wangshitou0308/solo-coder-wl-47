from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import WaterPoint, WaterPointStatus, User
from app.schemas.water_point import WaterPointCreate, WaterPointUpdate, WaterPointOut, WaterPointAreaGroup
from app.utils.security import get_current_user
from app.utils.permissions import require_admin, require_inspector_or_above, filter_by_area

router = APIRouter(prefix="/api/water-points", tags=["直饮水点管理"])


@router.post("", response_model=WaterPointOut, status_code=status.HTTP_201_CREATED)
def create_water_point(
    water_point_in: WaterPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inspector_or_above),
):
    existing = db.query(WaterPoint).filter(WaterPoint.equipment_no == water_point_in.equipment_no).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="设备编号已存在")
    water_point = WaterPoint(**water_point_in.model_dump())
    db.add(water_point)
    db.commit()
    db.refresh(water_point)
    return water_point


@router.get("", response_model=list[WaterPointOut])
def list_water_points(
    area: str = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WaterPoint)
    query = filter_by_area(query, current_user, WaterPoint.area)
    if area:
        query = query.filter(WaterPoint.area == area)
    return query.all()


@router.get("/group/by-area", response_model=list[WaterPointAreaGroup])
def group_water_points_by_area(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WaterPoint.area, func.count(WaterPoint.id).label("count"))
    query = filter_by_area(query, current_user, WaterPoint.area)
    results = query.group_by(WaterPoint.area).all()
    return [WaterPointAreaGroup(area=row.area, count=row.count) for row in results]


@router.get("/{water_point_id}", response_model=WaterPointOut)
def get_water_point(
    water_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="直饮水点不存在")
    return water_point


@router.put("/{water_point_id}", response_model=WaterPointOut)
def update_water_point(
    water_point_id: int,
    water_point_in: WaterPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="直饮水点不存在")
    update_data = water_point_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(water_point, field, value)
    db.commit()
    db.refresh(water_point)
    return water_point


@router.delete("/{water_point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_water_point(
    water_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="直饮水点不存在")
    db.delete(water_point)
    db.commit()
