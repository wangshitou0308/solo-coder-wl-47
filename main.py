from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.models import models
from app.routers import auth, water_point, inspection, filter_management, water_quality, work_order, citizen_report, dashboard

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="城市公共直饮水设施巡检与滤芯更换追踪服务",
    description="城市公园、广场、绿道等公共直饮水点的日常巡检与滤芯维护管理后端API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(water_point.router)
app.include_router(inspection.router)
app.include_router(filter_management.router)
app.include_router(water_quality.router)
app.include_router(work_order.router)
app.include_router(citizen_report.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"message": "城市公共直饮水设施巡检与滤芯更换追踪服务 API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
