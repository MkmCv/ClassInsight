"""
首页/仪表盘 API 路由
"""
from datetime import datetime, date, time
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ....core.database import get_db
from ....models.user import User
from ....models.video import Video, VideoStatus
from ....models.schedule import Schedule
from ....models.analysis import AnalysisSummary
from ...deps import get_current_user

router = APIRouter()


@router.get("/schedule")
async def get_today_schedule(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取今日课程表
    """
    today = datetime.now()
    day_of_week = today.weekday()  # 0-6 表示周一到周日
    current_time = today.time()
    
    # 查询今日课程
    result = await db.execute(
        select(Schedule)
        .where(
            and_(
                Schedule.user_id == current_user.id,
                Schedule.day_of_week == day_of_week
            )
        )
        .order_by(Schedule.start_time)
    )
    schedules = result.scalars().all()
    
    schedule_list = []
    for s in schedules:
        # 判断课程状态
        if current_time > s.end_time:
            status = "finished"
        elif current_time >= s.start_time:
            status = "ongoing"
        else:
            status = "upcoming"
        
        schedule_list.append({
            "time": f"{s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}",
            "subject": s.course_name,
            "class": s.class_name,
            "status": status
        })
    
    return {"schedule": schedule_list}


@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取首页核心指标卡片数据
    """
    # 查询待处理视频数量
    result = await db.execute(
        select(func.count(Video.id))
        .where(
            and_(
                Video.user_id == current_user.id,
                Video.status.in_([VideoStatus.UPLOADED.value, VideoStatus.PROCESSING.value])
            )
        )
    )
    pending_videos = result.scalar() or 0
    
    # 查询最近的分析汇总数据来计算平均指标
    result = await db.execute(
        select(AnalysisSummary)
        .join(Video, Video.id == AnalysisSummary.video_id)
        .where(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
        .limit(10)
    )
    summaries = result.scalars().all()
    
    # 计算平均互动率和专注度
    if summaries:
        avg_interaction = sum(s.interaction_rate or 0 for s in summaries) / len(summaries)
        avg_attention = sum(s.attention_rate or 0 for s in summaries) / len(summaries)
        
        # 简单计算环比（与前一半数据对比）
        mid = len(summaries) // 2
        if mid > 0:
            recent_interaction = sum(s.interaction_rate or 0 for s in summaries[:mid]) / mid
            older_interaction = sum(s.interaction_rate or 0 for s in summaries[mid:]) / (len(summaries) - mid)
            interaction_delta = recent_interaction - older_interaction
            
            recent_attention = sum(s.attention_rate or 0 for s in summaries[:mid]) / mid
            older_attention = sum(s.attention_rate or 0 for s in summaries[mid:]) / (len(summaries) - mid)
            attention_delta = recent_attention - older_attention
        else:
            interaction_delta = 0
            attention_delta = 0
    else:
        avg_interaction = 0
        avg_attention = 0
        interaction_delta = 0
        attention_delta = 0
    
    return {
        "interaction_rate": {
            "value": f"{avg_interaction * 100:.0f}%",
            "delta": f"{'+' if interaction_delta >= 0 else ''}{interaction_delta * 100:.0f}%"
        },
        "focus_rate": {
            "value": f"{avg_attention * 100:.0f}%",
            "delta": f"{'+' if attention_delta >= 0 else ''}{attention_delta * 100:.0f}%"
        },
        "pending_videos": pending_videos
    }


@router.get("/recent-videos")
async def get_recent_videos(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近的视频列表
    """
    result = await db.execute(
        select(Video)
        .where(Video.user_id == current_user.id)
        .order_by(Video.created_at.desc())
        .limit(limit)
    )
    videos = result.scalars().all()
    
    return {
        "videos": [
            {
                "video_id": v.id,
                "filename": v.filename,
                "class_name": v.class_name,
                "course_name": v.course_name,
                "status": v.status,
                "created_at": v.created_at.isoformat()
            }
            for v in videos
        ]
    }


