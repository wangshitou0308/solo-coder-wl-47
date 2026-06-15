from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import WaterQualityTest, WaterQualityResult, WorkOrder, WorkOrderType, WorkOrderStatus, WaterPoint, WaterPointStatus, User
from app.schemas.water_quality import WaterQualityTestCreate, WaterQualityTestOut
from app.utils.security import get_current_user
from app.utils.permissions import require_water_tester_or_above, filter_by_area
import random
from datetime import datetime

router = APIRouter(prefix="/api/water-quality", tags=["水质抽检管理"])


@router.post("", response_model=WaterQualityTestOut, status_code=status.HTTP_201_CREATED)
def create_water_quality_test(test_in: WaterQualityTestCreate, db: Session = Depends(get_db), current_user: User = Depends(require_water_tester_or_above)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == test_in.water_point_id).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")

    test = WaterQualityTest(
        water_point_id=test_in.water_point_id,
        tester_id=current_user.id,
        sample_date=test_in.sample_date,
        report_no=test_in.report_no,
        colony_count=test_in.colony_count,
        total_coliform=test_in.total_coliform,
        heavy_metal=test_in.heavy_metal,
        ph_value=test_in.ph_value,
        other_indicators=test_in.other_indicators,
        result=test_in.result,
        remark=test_in.remark,
    )
    db.add(test)
    db.flush()

    if test_in.result == WaterQualityResult.UNQUALIFIED:
        water_point.status = WaterPointStatus.DISABLED

        order_no = "WO" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
        description = f"水质检测不合格，检测报告编号：{test_in.report_no}，检测结果：不合格，饮水点已强制关停"
        work_order = WorkOrder(
            order_no=order_no,
            water_point_id=test_in.water_point_id,
            order_type=WorkOrderType.EMERGENCY,
            status=WorkOrderStatus.PENDING,
            description=description,
            created_by=current_user.id,
        )
        db.add(work_order)

    db.commit()
    db.refresh(test)
    return test


@router.get("", response_model=list[WaterQualityTestOut])
def list_water_quality_tests(water_point_id: int = Query(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(WaterQualityTest).join(WaterPoint, WaterQualityTest.water_point_id == WaterPoint.id)
    query = filter_by_area(query, current_user, WaterPoint.area)
    if water_point_id is not None:
        query = query.filter(WaterQualityTest.water_point_id == water_point_id)
    query = query.order_by(WaterQualityTest.created_at.desc())
    return query.all()


@router.get("/water-point/{wp_id}", response_model=list[WaterQualityTestOut])
def list_tests_by_water_point(wp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    water_point = db.query(WaterPoint).filter(WaterPoint.id == wp_id)
    water_point = filter_by_area(water_point, current_user, WaterPoint.area).first()
    if not water_point:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="饮水点不存在")
    tests = db.query(WaterQualityTest).filter(WaterQualityTest.water_point_id == wp_id).order_by(WaterQualityTest.created_at.desc()).all()
    return tests


@router.get("/{test_id}", response_model=WaterQualityTestOut)
def get_water_quality_test(test_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    test = db.query(WaterQualityTest).join(WaterPoint, WaterQualityTest.water_point_id == WaterPoint.id).filter(WaterQualityTest.id == test_id)
    test = filter_by_area(test, current_user, WaterPoint.area).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="水质检测记录不存在")
    return test
