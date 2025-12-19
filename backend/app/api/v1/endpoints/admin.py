"""
管理员 API 路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ....core.database import get_db
from ....core.security import get_password_hash
from ....models.user import User, UserRole
from ....models.video import Video, VideoStatus
from ....models.analysis import AnalysisSummary
from ....schemas.user import UserCreate, UserResponse
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
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户列表（管理员专用）
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **role**: 按角色筛选 (teacher/admin)
    """
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    
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
    role: Optional[str] = None,
    unit: Optional[str] = None,
    class_name: Optional[str] = None,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户信息（管理员专用）
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    if role and role in [UserRole.TEACHER.value, UserRole.ADMIN.value]:
        user.role = role
    if unit is not None:
        user.unit = unit
    if class_name is not None:
        user.class_name = class_name
    
    await db.commit()
    
    return {"message": "用户信息已更新"}


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


