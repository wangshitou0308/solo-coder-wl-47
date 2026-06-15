import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models.models import User, UserRole, WaterPoint, WaterPointStatus, FilterRecord
from app.utils.security import get_password_hash
from datetime import date


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                real_name="系统管理员",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)

            inspector = User(
                username="inspector01",
                hashed_password=get_password_hash("123456"),
                real_name="张巡检",
                role=UserRole.INSPECTOR,
                area="东湖区",
                phone="13800000001",
                is_active=True,
            )
            db.add(inspector)

            supervisor = User(
                username="supervisor01",
                hashed_password=get_password_hash("123456"),
                real_name="李主管",
                role=UserRole.MAINTENANCE_SUPERVISOR,
                area="东湖区",
                phone="13800000002",
                is_active=True,
            )
            db.add(supervisor)

            tester = User(
                username="tester01",
                hashed_password=get_password_hash("123456"),
                real_name="王检测",
                role=UserRole.WATER_QUALITY_TESTER,
                area="西湖区",
                phone="13800000003",
                is_active=True,
            )
            db.add(tester)

            wp1 = WaterPoint(
                equipment_no="WP-DH-001",
                name="东湖公园南门直饮水点",
                area="东湖区",
                address="东湖公园南门入口",
                longitude=115.8921,
                latitude=28.6760,
                model="ZYS-A100",
                install_date=date(2024, 3, 15),
                filter_spec="PP棉+活性炭+RO膜",
                rated_water_capacity=5000.0,
                status=WaterPointStatus.ONLINE,
            )
            db.add(wp1)

            wp2 = WaterPoint(
                equipment_no="WP-XH-001",
                name="西湖广场直饮水点",
                area="西湖区",
                address="西湖广场中央",
                longitude=115.8821,
                latitude=28.6660,
                model="ZYS-B200",
                install_date=date(2024, 5, 20),
                filter_spec="PP棉+超滤膜",
                rated_water_capacity=3000.0,
                status=WaterPointStatus.ONLINE,
            )
            db.add(wp2)

            wp3 = WaterPoint(
                equipment_no="WP-DH-002",
                name="东湖绿道中段直饮水点",
                area="东湖区",
                address="东湖绿道2公里处",
                longitude=115.8950,
                latitude=28.6780,
                model="ZYS-A100",
                install_date=date(2024, 6, 10),
                filter_spec="PP棉+活性炭+RO膜",
                rated_water_capacity=5000.0,
                status=WaterPointStatus.ONLINE,
            )
            db.add(wp3)

            db.flush()

            fr1 = FilterRecord(
                water_point_id=wp1.id,
                current_batch="FC-2024-001",
                install_date=date(2024, 3, 15),
                rated_water_capacity=5000.0,
                cumulative_days=180,
                cumulative_water_usage=2500.0,
                remaining_life_percent=50.0,
                last_replacement_date=date(2024, 3, 15),
            )
            db.add(fr1)

            fr2 = FilterRecord(
                water_point_id=wp2.id,
                current_batch="FC-2024-002",
                install_date=date(2024, 5, 20),
                rated_water_capacity=3000.0,
                cumulative_days=90,
                cumulative_water_usage=2800.0,
                remaining_life_percent=6.67,
                last_replacement_date=date(2024, 5, 20),
            )
            db.add(fr2)

            db.commit()
            print("数据库初始化成功！")
            print("默认账号：")
            print("  管理员: admin / admin123")
            print("  巡检员: inspector01 / 123456 (东湖区)")
            print("  运维主管: supervisor01 / 123456 (东湖区)")
            print("  水质检测员: tester01 / 123456 (西湖区)")
        else:
            print("数据库已初始化，跳过。")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
