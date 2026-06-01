"""
管理员 API 路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from ....core.database import get_db
from ....core.security import get_password_hash
from ....core.config import settings
from ....models.user import User, UserRole
from ....models.video import Video, VideoStatus
from ....models.analysis import AnalysisSummary
from ....models.login_attempt import LoginAttempt
from ....models.login_history import LoginHistory
from ....schemas.user import UserCreate, UserResponse, UserUpdate
from ...deps import get_current_user

router = APIRouter()


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """验证当前用户是否为管理员"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: Optional[str] = None,
    search: Optional[str] = Query(None, description="搜索关键词（用户名/邮箱）"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户列表（管理员专用）
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **role**: 按角色筛选 (teacher/admin)
    - **search**: 搜索关键词（用户名或邮箱）
    - **is_active**: 按状态筛选（true=启用, false=禁用）
    """
    query = select(User)
    
    # 排除超级管理员（管理员不能管理超级管理员）
    query = query.where(User.role != UserRole.SUPER_ADMIN.value)
    
    # 角色筛选
    if role:
        query = query.where(User.role == role)
    
    # 状态筛选
    if is_active is not None:
        query = query.where(User.is_active == (1 if is_active else 0))
    
    # 搜索（用户名或邮箱）
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.username.like(search_pattern)) | 
            (User.email.like(search_pattern))
        )
    
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [UserResponse.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户详情（管理员专用）
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息（管理员专用）
    支持更新：邮箱、角色、单位、班级、状态
    """
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 禁止管理员修改超级管理员
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能修改超级管理员"
        )
    
    # 更新邮箱（需要检查唯一性）
    if user_data.email is not None and user_data.email != user.email:
        # 检查邮箱是否已被其他用户使用
        email_check = await db.execute(
            select(User).where(User.email == user_data.email, User.id != user_id)
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="邮箱已被其他用户使用"
            )
        user.email = user_data.email
    
    # 更新角色（禁止设置为超级管理员）
    if user_data.role is not None:
        if user_data.role == UserRole.SUPER_ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员不能将用户设置为超级管理员"
            )
        if user_data.role in [UserRole.TEACHER.value, UserRole.ADMIN.value]:
            user.role = user_data.role
    
    # 更新单位
    if user_data.unit is not None:
        user.unit = user_data.unit
    
    # 更新班级
    if user_data.class_name is not None:
        user.class_name = user_data.class_name
    
    # 更新状态
    if user_data.is_active is not None:
        user.is_active = 1 if user_data.is_active else 0
    
    await db.commit()
    await db.refresh(user)
    
    return {"message": "用户信息已更新", "user": UserResponse.model_validate(user)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除用户（管理员专用）
    """
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 禁止管理员删除超级管理员
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能删除超级管理员"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "用户已删除"}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=8, description="新密码，至少8位"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重置用户密码（管理员专用）
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 禁止管理员重置超级管理员密码
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能重置超级管理员密码"
        )
    
    user.password_hash = get_password_hash(new_password)
    await db.commit()
    
    return {"message": "密码已重置"}


@router.get("/statistics")
async def get_system_statistics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取系统统计数据（管理员专用）
    """
    # 用户统计
    user_count_result = await db.execute(select(func.count(User.id)))
    total_users = user_count_result.scalar() or 0
    
    teacher_count_result = await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.TEACHER.value)
    )
    teacher_count = teacher_count_result.scalar() or 0
    
    admin_count_result = await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN.value)
    )
    admin_count = admin_count_result.scalar() or 0
    
    # 视频统计
    video_count_result = await db.execute(select(func.count(Video.id)))
    total_videos = video_count_result.scalar() or 0
    
    completed_result = await db.execute(
        select(func.count(Video.id)).where(Video.status == VideoStatus.COMPLETED.value)
    )
    completed_videos = completed_result.scalar() or 0
    
    processing_result = await db.execute(
        select(func.count(Video.id)).where(Video.status == VideoStatus.PROCESSING.value)
    )
    processing_videos = processing_result.scalar() or 0
    
    failed_result = await db.execute(
        select(func.count(Video.id)).where(Video.status == VideoStatus.FAILED.value)
    )
    failed_videos = failed_result.scalar() or 0
    
    # 分析统计
    analysis_count_result = await db.execute(select(func.count(AnalysisSummary.id)))
    total_analyses = analysis_count_result.scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "teachers": teacher_count,
            "admins": admin_count
        },
        "videos": {
            "total": total_videos,
            "completed": completed_videos,
            "processing": processing_videos,
            "failed": failed_videos
        },
        "analyses": {
            "total": total_analyses
        }
    }


@router.get("/videos")
async def get_all_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有视频列表（管理员专用）
    """
    query = select(Video)
    
    if status:
        query = query.where(Video.status == status)
    
    # 计算总数
    count_query = select(func.count(Video.id))
    if status:
        count_query = count_query.where(Video.status == status)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(Video.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "video_id": v.id,
                "user_id": v.user_id,
                "filename": v.filename,
                "class_name": v.class_name,
                "course_name": v.course_name,
                "lesson_date": v.lesson_date.isoformat() if v.lesson_date else None,
                "status": v.status,
                "duration": v.duration,
                "created_at": v.created_at.isoformat()
            }
            for v in videos
        ]
    }


@router.delete("/videos/{video_id}")
async def admin_delete_video(
    video_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除任意视频（管理员专用）
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    await db.delete(video)
    await db.commit()
    
    return {"message": "视频已删除"}


# ==================== 批量操作 ====================

class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    user_ids: List[int] = Body(..., description="要删除的用户ID列表")


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    user_ids: List[int] = Body(..., description="要更新的用户ID列表")
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/users/batch-delete")
async def batch_delete_users(
    request: BatchDeleteRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量删除用户（管理员专用）
    """
    # 不能删除自己
    if admin.id in request.user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 查找要删除的用户
    result = await db.execute(
        select(User).where(User.id.in_(request.user_ids))
    )
    users = result.scalars().all()
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到要删除的用户"
        )
    
    # 检查是否包含超级管理员
    super_admins = [u for u in users if u.role == UserRole.SUPER_ADMIN.value]
    if super_admins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能删除超级管理员"
        )
    
    # 删除用户
    for user in users:
        await db.delete(user)
    
    await db.commit()
    
    return {"message": f"已删除 {len(users)} 个用户"}


@router.post("/users/batch-update")
async def batch_update_users(
    request: BatchUpdateRequest,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量更新用户（管理员专用）
    支持批量修改角色和状态
    """
    # 查找要更新的用户
    result = await db.execute(
        select(User).where(User.id.in_(request.user_ids))
    )
    users = result.scalars().all()
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到要更新的用户"
        )
    
    # 批量更新（跳过超级管理员）
    updated_count = 0
    for user in users:
        # 跳过超级管理员
        if user.role == UserRole.SUPER_ADMIN.value:
            continue
        
        updated = False
        
        if request.role and request.role in [UserRole.TEACHER.value, UserRole.ADMIN.value]:
            user.role = request.role
            updated = True
        
        if request.is_active is not None:
            user.is_active = 1 if request.is_active else 0
            updated = True
        
        if updated:
            updated_count += 1
    
    await db.commit()
    
    return {"message": f"已更新 {updated_count} 个用户"}


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    切换用户状态（启用/禁用）
    """
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 禁止管理员修改超级管理员状态
    if user.role == UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能修改超级管理员状态"
        )
    
    # 切换状态
    user.is_active = 0 if user.is_active == 1 else 1
    await db.commit()
    
    status_text = "启用" if user.is_active == 1 else "禁用"
    return {"message": f"用户已{status_text}", "is_active": bool(user.is_active)}


# ==================== 登录失败记录管理 ====================

@router.get("/login-attempts/{username}")
async def get_user_login_attempts(
    username: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的登录失败记录
    """
    result = await db.execute(
        select(LoginAttempt).where(LoginAttempt.username == username)
    )
    attempts = result.scalars().all()
    
    return [
        {
            "id": a.id,
            "username": a.username,
            "ip_address": a.ip_address,
            "failed_count": a.failed_count,
            "locked_until": a.locked_until.isoformat() if a.locked_until else None,
            "last_attempt": a.last_attempt.isoformat(),
            "created_at": a.created_at.isoformat()
        }
        for a in attempts
    ]


@router.delete("/login-attempts/{username}")
async def clear_user_login_attempts(
    username: str,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    清除指定用户的登录失败记录（解锁账户）
    """
    result = await db.execute(
        select(LoginAttempt).where(LoginAttempt.username == username)
    )
    attempts = result.scalars().all()
    
    if not attempts:
        return {"message": "该用户没有登录失败记录"}
    
    count = len(attempts)
    for attempt in attempts:
        await db.delete(attempt)
    
    await db.commit()
    
    return {"message": f"已清除 {count} 条登录失败记录，账户已解锁"}


@router.get("/login-attempts")
async def get_all_login_attempts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    username: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有登录失败记录（管理员查看）
    """
    query = select(LoginAttempt)
    
    if username:
        query = query.where(LoginAttempt.username.ilike(f"%{username}%"))
    
    # 总数
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    # 分页
    query = query.order_by(LoginAttempt.last_attempt.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    attempts = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": a.id,
                "username": a.username,
                "ip_address": a.ip_address,
                "failed_count": a.failed_count,
                "locked_until": a.locked_until.isoformat() if a.locked_until else None,
                "last_attempt": a.last_attempt.isoformat(),
                "created_at": a.created_at.isoformat()
            }
            for a in attempts
        ]
    }


@router.get("/login-security-config")
async def get_login_security_config(
    admin: User = Depends(get_admin_user)
):
    """
    获取登录安全配置（当前设置）
    """
    return {
        "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
        "lockout_minutes": settings.LOGIN_LOCKOUT_MINUTES,
        "captcha_required_after": settings.CAPTCHA_REQUIRED_AFTER,
        "note": "配置修改需要重启服务生效"
    }


@router.get("/users/{user_id}/login-history")
async def get_user_login_history(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的登录历史记录
    """
    result = await db.execute(
        select(LoginHistory)
        .where(LoginHistory.user_id == user_id)
        .order_by(LoginHistory.login_time.desc())
        .limit(limit)
    )
    histories = result.scalars().all()
    
    return [
        {
            "id": h.id,
            "username": h.username,
            "ip_address": h.ip_address,
            "user_agent": h.user_agent,
            "login_time": h.login_time.isoformat(),
            "status": h.status,
            "failure_reason": h.failure_reason
        }
        for h in histories
    ]













