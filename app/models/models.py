import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Enum, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    INSPECTOR = "inspector"
    MAINTENANCE_SUPERVISOR = "maintenance_supervisor"
    WATER_QUALITY_TESTER = "water_quality_tester"
    ADMIN = "admin"


class WorkOrderType(str, enum.Enum):
    REPAIR = "repair"
    FILTER_REPLACEMENT = "filter_replacement"
    EMERGENCY = "emergency"
    COMPLAINT = "complaint"


class WorkOrderStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class WaterPointStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


class InspectionResult(str, enum.Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"


class WaterQualityResult(str, enum.Enum):
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"


class FaultType(str, enum.Enum):
    NO_WATER = "no_water"
    WATER_QUALITY_ABNORMAL = "water_quality_abnormal"
    APPEARANCE_DAMAGED = "appearance_damaged"
    LEAKAGE = "leakage"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    real_name = Column(String(50), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    area = Column(String(100))
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class WaterPoint(Base):
    __tablename__ = "water_points"

    id = Column(Integer, primary_key=True, index=True)
    equipment_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    area = Column(String(100), index=True, nullable=False)
    address = Column(String(200), nullable=False)
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    model = Column(String(100), nullable=False)
    install_date = Column(Date, nullable=False)
    filter_spec = Column(String(100), nullable=False)
    rated_water_capacity = Column(Float, nullable=False)
    status = Column(Enum(WaterPointStatus), default=WaterPointStatus.ONLINE)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    inspections = relationship("Inspection", back_populates="water_point")
    filter_records = relationship("FilterRecord", back_populates="water_point")
    filter_replacements = relationship("FilterReplacement", back_populates="water_point")
    water_quality_tests = relationship("WaterQualityTest", back_populates="water_point")
    work_orders = relationship("WorkOrder", back_populates="water_point")
    citizen_reports = relationship("CitizenReport", back_populates="water_point")


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    water_point_id = Column(Integer, ForeignKey("water_points.id"), nullable=False)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    inspection_date = Column(Date, nullable=False)
    appearance_ok = Column(Boolean, nullable=False)
    water_output_ok = Column(Boolean, nullable=False)
    button_sensitivity_ok = Column(Boolean, nullable=False)
    drainage_ok = Column(Boolean, nullable=False)
    tds_value = Column(Float, nullable=False)
    tds_threshold = Column(Float, default=50.0)
    result = Column(Enum(InspectionResult), nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    water_point = relationship("WaterPoint", back_populates="inspections")
    inspector = relationship("User")


class FilterRecord(Base):
    __tablename__ = "filter_records"

    id = Column(Integer, primary_key=True, index=True)
    water_point_id = Column(Integer, ForeignKey("water_points.id"), nullable=False)
    current_batch = Column(String(50), nullable=False)
    install_date = Column(Date, nullable=False)
    rated_water_capacity = Column(Float, nullable=False)
    cumulative_days = Column(Integer, default=0)
    cumulative_water_usage = Column(Float, default=0.0)
    remaining_life_percent = Column(Float, default=100.0)
    last_replacement_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    water_point = relationship("WaterPoint", back_populates="filter_records")


class FilterReplacement(Base):
    __tablename__ = "filter_replacements"

    id = Column(Integer, primary_key=True, index=True)
    water_point_id = Column(Integer, ForeignKey("water_points.id"), nullable=False)
    old_batch = Column(String(50), nullable=False)
    new_batch = Column(String(50), nullable=False)
    replacement_date = Column(Date, nullable=False)
    replaced_by = Column(String(50), nullable=False)
    replaced_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    water_point = relationship("WaterPoint", back_populates="filter_replacements")
    operator = relationship("User")


class WaterQualityTest(Base):
    __tablename__ = "water_quality_tests"

    id = Column(Integer, primary_key=True, index=True)
    water_point_id = Column(Integer, ForeignKey("water_points.id"), nullable=False)
    tester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sample_date = Column(Date, nullable=False)
    report_no = Column(String(50), nullable=False)
    colony_count = Column(Float)
    total_coliform = Column(Float)
    heavy_metal = Column(Float)
    ph_value = Column(Float)
    other_indicators = Column(Text)
    result = Column(Enum(WaterQualityResult), nullable=False)
    remark = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    water_point = relationship("WaterPoint", back_populates="water_quality_tests")
    tester = relationship("User")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    water_point_id = Column(Integer, ForeignKey("water_points.id"), nullable=False)
    order_type = Column(Enum(WorkOrderType), nullable=False)
    status = Column(Enum(WorkOrderStatus), default=WorkOrderStatus.PENDING)
    description = Column(Text, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    completed_at = Column(DateTime)
    feedback = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    water_point = relationship("WaterPoint", back_populates="work_orders")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)
    water_point_id = Column(Integer, ForeignKey("water_points.id"), nullable=True)
    reporter_name = Column(String(50))
    reporter_phone = Column(String(20))
    fault_type = Column(Enum(FaultType), nullable=False)
    description = Column(Text)
    longitude = Column(Float)
    latitude = Column(Float)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"))
    is_resolved = Column(Boolean, default=False)
    feedback = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    water_point = relationship("WaterPoint", back_populates="citizen_reports")
    work_order = relationship("WorkOrder")
