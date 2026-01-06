"""
课表管理 API 路由
"""
from typing import Optional, List
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ....core.database import get_db
from ....models.user import User, UserRole
from ....models.schedule import Schedule
from ....schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, 
    ScheduleWithStatus, DayScheduleResponse, WeekScheduleResponse
)
from ...deps import get_current_user

router = APIRouter()

# 星期名称映射
DAY_NAMES = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def get_week_range(target_date: date) -> tuple:
    """获取指定日期所在周的起止日期（周一到周日）"""
    # 获取周一
    days_since_monday = target_date.weekday()
    week_start = target_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_schedule_status(schedule: Schedule, target_date: date) -> str:
    """计算课程状态：已结束/进行中/待开始"""
    now = datetime.now()
    today = now.date()
    current_time = now.time()
    
    # 计算课程的实际日期
    days_diff = schedule.day_of_week - target_date.weekday()
    schedule_date = target_date + timedelta(days=days_diff)
    
    if schedule_date < today:
        return "finished"
    elif schedule_date > today:
        return "upcoming"
    else:
        # 今天，比较时间
        if current_time < schedule.start_time:
            return "upcoming"
        elif current_time > schedule.end_time:
            return "finished"
        else:
            return "ongoing"


# ==================== 教师查询自己的课表 ====================

@router.get("/my", response_model=List[ScheduleResponse])
async def get_my_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前教师的所有课程安排
    """
    result = await db.execute(
        select(Schedule)
        .where(Schedule.user_id == current_user.id)
        .order_by(Schedule.day_of_week, Schedule.start_time)
    )
    schedules = result.scalars().all()
    
    return [
        ScheduleResponse(
            id=s.id,
            user_id=s.user_id,
            course_name=s.course_name,
            class_name=s.class_name,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            teacher_name=current_user.username,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in schedules
    ]


@router.get("/week", response_model=WeekScheduleResponse)
async def get_week_schedule(
    target_date: date = Query(default=None, description="周内任意一天，默认今天"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定周的课表（智能日历用）
    
    返回该周7天的课程安排，包含每节课的状态
    """
    if target_date is None:
        target_date = date.today()
    
    week_start, week_end = get_week_range(target_date)
    
    # 获取用户课表
    result = await db.execute(
        select(Schedule)
        .where(Schedule.user_id == current_user.id)
        .order_by(Schedule.day_of_week, Schedule.start_time)
    )
    schedules = result.scalars().all()
    
    # 构建7天的数据
    days = []
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        day_schedules = [s for s in schedules if s.day_of_week == i]
        
        schedule_items = []
        for s in day_schedules:
            schedule_items.append(ScheduleWithStatus(
                id=s.id,
                user_id=s.user_id,
                course_name=s.course_name,
                class_name=s.class_name,
                day_of_week=s.day_of_week,
                start_time=s.start_time,
                end_time=s.end_time,
                teacher_name=current_user.username,
                created_at=s.created_at,
                updated_at=s.updated_at,
                status=get_schedule_status(s, week_start),
                schedule_date=current_date
            ))
        
        days.append(DayScheduleResponse(
            date=current_date,
            day_of_week=i,
            day_name=DAY_NAMES[i],
            schedules=schedule_items
        ))
    
    return WeekScheduleResponse(
        week_start=week_start,
        week_end=week_end,
        days=days
    )


@router.get("/today", response_model=List[ScheduleWithStatus])
async def get_today_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日课表（首页用）
    """
    today = date.today()
    day_of_week = today.weekday()
    
    result = await db.execute(
        select(Schedule)
        .where(and_(
            Schedule.user_id == current_user.id,
            Schedule.day_of_week == day_of_week
        ))
        .order_by(Schedule.start_time)
    )
    schedules = result.scalars().all()
    
    week_start, _ = get_week_range(today)
    
    return [
        ScheduleWithStatus(
            id=s.id,
            user_id=s.user_id,
            course_name=s.course_name,
            class_name=s.class_name,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            teacher_name=current_user.username,
            created_at=s.created_at,
            updated_at=s.updated_at,
            status=get_schedule_status(s, week_start),
            schedule_date=today
        )
        for s in schedules
    ]


# ==================== 管理员排课功能 ====================

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """验证当前用户是否为管理员"""
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


@router.get("/all", response_model=List[ScheduleResponse])
async def get_all_schedules(
    user_id: Optional[int] = Query(None, description="按教师ID筛选"),
    day_of_week: Optional[int] = Query(None, ge=0, le=6, description="按星期筛选"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有课程安排（管理员专用）
    """
    query = select(Schedule, User.username).join(User, Schedule.user_id == User.id)
    
    if user_id:
        query = query.where(Schedule.user_id == user_id)
    if day_of_week is not None:
        query = query.where(Schedule.day_of_week == day_of_week)
    
    query = query.order_by(Schedule.day_of_week, Schedule.start_time)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        ScheduleResponse(
            id=schedule.id,
            user_id=schedule.user_id,
            course_name=schedule.course_name,
            class_name=schedule.class_name,
            day_of_week=schedule.day_of_week,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            teacher_name=username,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        for schedule, username in rows
    ]


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建课程安排（管理员排课）
    """
    # 确定教师ID
    teacher_id = schedule_data.user_id
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须指定教师ID"
        )
    
    # 验证教师存在
    result = await db.execute(select(User).where(User.id == teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教师不存在"
        )
    
    # 检查时间冲突
    result = await db.execute(
        select(Schedule).where(and_(
            Schedule.user_id == teacher_id,
            Schedule.day_of_week == schedule_data.day_of_week,
            # 时间段有重叠
            Schedule.start_time < schedule_data.end_time,
            Schedule.end_time > schedule_data.start_time
        ))
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该时间段已有课程安排"
        )
    
    # 创建课程
    schedule = Schedule(
        user_id=teacher_id,
        course_name=schedule_data.course_name,
        class_name=schedule_data.class_name,
        day_of_week=schedule_data.day_of_week,
        start_time=schedule_data.start_time,
        end_time=schedule_data.end_time
    )
    
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    
    return ScheduleResponse(
        id=schedule.id,
        user_id=schedule.user_id,
        course_name=schedule.course_name,
        class_name=schedule.class_name,
        day_of_week=schedule.day_of_week,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        teacher_name=teacher.username,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at
    )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新课程安排（管理员调课）
    """
    result = await db.execute(
        select(Schedule, User.username)
        .join(User, Schedule.user_id == User.id)
        .where(Schedule.id == schedule_id)
    )
    row = result.first()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在"
        )
    
    schedule, teacher_name = row
    
    # 更新字段
    if schedule_data.course_name is not None:
        schedule.course_name = schedule_data.course_name
    if schedule_data.class_name is not None:
        schedule.class_name = schedule_data.class_name
    if schedule_data.day_of_week is not None:
        schedule.day_of_week = schedule_data.day_of_week
    if schedule_data.start_time is not None:
        schedule.start_time = schedule_data.start_time
    if schedule_data.end_time is not None:
        schedule.end_time = schedule_data.end_time
    
    await db.commit()
    await db.refresh(schedule)
    
    return ScheduleResponse(
        id=schedule.id,
        user_id=schedule.user_id,
        course_name=schedule.course_name,
        class_name=schedule.class_name,
        day_of_week=schedule.day_of_week,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        teacher_name=teacher_name,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at
    )


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除课程安排（管理员取消课程）
    """
    result = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在"
        )
    
    await db.delete(schedule)
    await db.commit()
    
    return {"message": "课程已删除"}


@router.get("/teachers", response_model=List[dict])
async def get_teachers_for_schedule(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取可排课的教师列表（管理员用）
    """
    result = await db.execute(
        select(User.id, User.username, User.unit, User.class_name)
        .where(User.role == UserRole.TEACHER.value)
        .order_by(User.username)
    )
    teachers = result.all()
    
    return [
        {
            "id": t.id,
            "username": t.username,
            "unit": t.unit,
            "class_name": t.class_name
        }
        for t in teachers
    ]

