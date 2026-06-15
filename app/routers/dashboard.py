from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from app.database import get_db
from app.models.models import (
    WaterPoint, WaterPointStatus, FilterRecord, Inspection,
    InspectionResult, WaterQualityTest, WaterQualityResult,
    CitizenReport, WorkOrder, WorkOrderStatus, User,
)
from app.schemas.dashboard import (
    DashboardData, AreaOnlineRate, FilterExpiryItem,
    InspectionCoverage, WaterQualityTrendItem, ComplaintStats,
)
from app.utils.security import get_current_user
from app.utils.permissions import filter_by_area
from datetime import datetime

router = APIRouter(prefix="/api/dashboard", tags=["数据看板"])


@router.get("", response_model=DashboardData)
def get_dashboard_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    area_online_rates = _build_area_online_rates(db, current_user)
    filter_expiry_list = _build_filter_expiry_list(db, current_user)
    inspection_coverage = _build_inspection_coverage(db, current_user, current_year, current_month)
    water_quality_trend = _build_water_quality_trend(db, current_user, current_year, current_month)
    complaint_stats = _build_complaint_stats(db, current_user, current_year, current_month)

    return DashboardData(
        area_online_rates=area_online_rates,
        filter_expiry_list=filter_expiry_list,
        inspection_coverage=inspection_coverage,
        water_quality_trend=water_quality_trend,
        complaint_stats=complaint_stats,
    )


def _build_area_online_rates(db: Session, current_user: User):
    wp_query = db.query(WaterPoint)
    wp_query = filter_by_area(wp_query, current_user, WaterPoint.area)

    area_total = wp_query.group_by(WaterPoint.area).with_entities(
        WaterPoint.area,
        func.count(WaterPoint.id).label("total"),
    ).all()

    area_online = wp_query.filter(
        WaterPoint.status == WaterPointStatus.ONLINE
    ).group_by(WaterPoint.area).with_entities(
        WaterPoint.area,
        func.count(WaterPoint.id).label("online"),
    ).all()

    online_map = {r.area: r.online for r in area_online}

    results = []
    for r in area_total:
        online = online_map.get(r.area, 0)
        rate = round(online / r.total, 4) if r.total > 0 else 0.0
        results.append(AreaOnlineRate(area=r.area, total=r.total, online=online, online_rate=rate))
    return results


def _build_filter_expiry_list(db: Session, current_user: User):
    query = (
        db.query(
            FilterRecord, WaterPoint.id.label("wp_id"),
            WaterPoint.equipment_no, WaterPoint.name, WaterPoint.area,
        )
        .join(WaterPoint, FilterRecord.water_point_id == WaterPoint.id)
        .filter(FilterRecord.remaining_life_percent < 30)
    )
    query = filter_by_area(query, current_user, WaterPoint.area)
    query = query.order_by(FilterRecord.remaining_life_percent.asc())
    rows = query.all()

    return [
        FilterExpiryItem(
            water_point_id=row.wp_id,
            equipment_no=row.equipment_no,
            name=row.name,
            area=row.area,
            remaining_life_percent=row.FilterRecord.remaining_life_percent,
            current_batch=row.FilterRecord.current_batch,
        )
        for row in rows
    ]


def _build_inspection_coverage(db: Session, current_user: User, current_year: int, current_month: int):
    wp_query = db.query(WaterPoint)
    wp_query = filter_by_area(wp_query, current_user, WaterPoint.area)
    total_points = wp_query.count()

    insp_query = (
        db.query(Inspection)
        .join(WaterPoint, Inspection.water_point_id == WaterPoint.id)
        .filter(
            extract("year", Inspection.inspection_date) == current_year,
            extract("month", Inspection.inspection_date) == current_month,
        )
    )
    insp_query = filter_by_area(insp_query, current_user, WaterPoint.area)

    inspected_points = insp_query.with_entities(
        func.count(func.distinct(Inspection.water_point_id))
    ).scalar() or 0

    coverage_rate = round(inspected_points / total_points, 4) if total_points > 0 else 0.0

    normal_count = insp_query.filter(
        Inspection.result == InspectionResult.NORMAL
    ).count()

    abnormal_count = insp_query.filter(
        Inspection.result == InspectionResult.ABNORMAL
    ).count()

    total_inspections = normal_count + abnormal_count
    anomaly_rate = round(abnormal_count / total_inspections, 4) if total_inspections > 0 else 0.0

    return InspectionCoverage(
        total_points=total_points,
        inspected_points=inspected_points,
        coverage_rate=coverage_rate,
        normal_count=normal_count,
        abnormal_count=abnormal_count,
        anomaly_rate=anomaly_rate,
    )


def _build_water_quality_trend(db: Session, current_user: User, current_year: int, current_month: int):
    results = []
    for i in range(5, -1, -1):
        y = current_year
        m = current_month - i
        while m <= 0:
            m += 12
            y -= 1
        month_str = f"{y:04d}-{m:02d}"

        q = (
            db.query(WaterQualityTest)
            .join(WaterPoint, WaterQualityTest.water_point_id == WaterPoint.id)
            .filter(
                extract("year", WaterQualityTest.sample_date) == y,
                extract("month", WaterQualityTest.sample_date) == m,
            )
        )
        q = filter_by_area(q, current_user, WaterPoint.area)

        total_tests = q.count()
        qualified_count = q.filter(
            WaterQualityTest.result == WaterQualityResult.QUALIFIED
        ).count()

        qualified_rate = round(qualified_count / total_tests, 4) if total_tests > 0 else 0.0

        results.append(WaterQualityTrendItem(
            month=month_str,
            total_tests=total_tests,
            qualified_count=qualified_count,
            qualified_rate=qualified_rate,
        ))
    return results


def _build_complaint_stats(db: Session, current_user: User, current_year: int, current_month: int):
    report_query = (
        db.query(CitizenReport)
        .join(WaterPoint, CitizenReport.water_point_id == WaterPoint.id)
        .filter(
            extract("year", CitizenReport.created_at) == current_year,
            extract("month", CitizenReport.created_at) == current_month,
        )
    )
    report_query = filter_by_area(report_query, current_user, WaterPoint.area)

    total_complaints = report_query.count()

    resolved_query = report_query.filter(CitizenReport.is_resolved == True)
    resolved_complaints = resolved_query.count()

    resolution_rate = round(resolved_complaints / total_complaints, 4) if total_complaints > 0 else 0.0

    avg_resolution_hours = None
    if resolved_complaints > 0:
        resolved_with_order = (
            resolved_query
            .join(WorkOrder, CitizenReport.work_order_id == WorkOrder.id)
            .filter(WorkOrder.completed_at.isnot(None))
            .with_entities(
                func.avg(
                    func.extract("epoch", WorkOrder.completed_at - CitizenReport.created_at) / 3600.0
                ).label("avg_hours")
            ).scalar()
        )
        if resolved_with_order is not None:
            avg_resolution_hours = round(float(resolved_with_order), 2)

    return ComplaintStats(
        total_complaints=total_complaints,
        resolved_complaints=resolved_complaints,
        avg_resolution_hours=avg_resolution_hours,
        resolution_rate=resolution_rate,
    )
