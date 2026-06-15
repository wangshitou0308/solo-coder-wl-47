from fastapi import Depends, HTTPException, status
from app.models.models import User, UserRole
from app.utils.security import get_current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅系统管理员可执行此操作")
    return current_user


def require_admin_or_supervisor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.MAINTENANCE_SUPERVISOR):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员或运维主管可执行此操作")
    return current_user


def require_inspector_or_above(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.INSPECTOR, UserRole.MAINTENANCE_SUPERVISOR, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    return current_user


def require_water_tester_or_above(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.WATER_QUALITY_TESTER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅水质检测员或管理员可执行此操作")
    return current_user


def filter_by_area(query, current_user: User, area_field):
    if current_user.role == UserRole.ADMIN:
        return query
    if current_user.area:
        return query.filter(area_field == current_user.area)
    return query
