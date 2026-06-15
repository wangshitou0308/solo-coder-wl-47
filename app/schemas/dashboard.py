from typing import List, Optional
from pydantic import BaseModel


class AreaOnlineRate(BaseModel):
    area: str
    total: int
    online: int
    online_rate: float


class FilterExpiryItem(BaseModel):
    water_point_id: int
    equipment_no: str
    name: str
    area: str
    remaining_life_percent: float
    current_batch: str


class InspectionCoverage(BaseModel):
    total_points: int
    inspected_points: int
    coverage_rate: float
    normal_count: int
    abnormal_count: int
    anomaly_rate: float


class WaterQualityTrendItem(BaseModel):
    month: str
    total_tests: int
    qualified_count: int
    qualified_rate: float


class ComplaintStats(BaseModel):
    total_complaints: int
    resolved_complaints: int
    avg_resolution_hours: Optional[float]
    resolution_rate: float


class DashboardData(BaseModel):
    area_online_rates: List[AreaOnlineRate]
    filter_expiry_list: List[FilterExpiryItem]
    inspection_coverage: InspectionCoverage
    water_quality_trend: List[WaterQualityTrendItem]
    complaint_stats: ComplaintStats
