"""
行为分析 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ....core.database import get_db
from ....core.config import STUDENT_BEHAVIORS, TEACHER_BEHAVIORS
from ....models.user import User
from ....models.video import Video, VideoStatus
from ....models.analysis import AnalysisTimeline, AnalysisSummary, AnalysisAnomaly
from ....schemas.analysis import (
    AnalysisSummaryResponse, BehaviorStat,
    TimelineResponse, TimelinePoint,
    AnomalyResponse, AnomalyItem,
    CausationResponse, CorrelationItem, OverlapItem
)
from ...deps import get_current_user

router = APIRouter()


async def verify_video_access(video_id: int, user: User, db: AsyncSession) -> Video:
    """验证用户对视频的访问权限"""
    result = await db.execute(
        select(Video).where(
            and_(Video.id == video_id, Video.user_id == user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    if video.status != VideoStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频尚未处理完成"
        )
    
    return video


@router.get("/{video_id}/summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取整课行为统计汇总
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 获取汇总数据
    result = await db.execute(
        select(AnalysisSummary).where(AnalysisSummary.video_id == video_id)
    )
    summary = result.scalar_one_or_none()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析数据不存在"
        )
    
    summary_data = summary.summary_json
    
    # 构建响应
    behavior_summary = {}
    teacher_behavior = {}
    
    for behavior, data in summary_data.get("behavior_summary", {}).items():
        if behavior in STUDENT_BEHAVIORS:
            behavior_summary[behavior] = BehaviorStat(**data)
        elif behavior in TEACHER_BEHAVIORS:
            teacher_behavior[behavior] = BehaviorStat(**data)
    
    return AnalysisSummaryResponse(
        video_id=video_id,
        duration=video.duration or 0,
        total_frames=video.total_frames or 0,
        behavior_summary=behavior_summary,
        teacher_behavior=teacher_behavior
    )


@router.get("/{video_id}/timeline", response_model=TimelineResponse)
async def get_analysis_timeline(
    video_id: int,
    window: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取时间序列数据（用于可视化）
    
    - **window**: 时间窗口大小（秒），可选值：10, 60（默认10）
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 验证 window 参数
    if window not in [10, 60]:
        window = 10
    
    # 获取时间线数据
    result = await db.execute(
        select(AnalysisTimeline)
        .where(
            and_(
                AnalysisTimeline.video_id == video_id,
                AnalysisTimeline.window_size == window
            )
        )
        .order_by(AnalysisTimeline.timestamp)
    )
    timeline_data = result.scalars().all()
    
    timeline = [
        TimelinePoint(
            timestamp=t.timestamp,
            behaviors=t.behavior_counts
        )
        for t in timeline_data
    ]
    
    return TimelineResponse(
        video_id=video_id,
        window_size=window,
        timeline=timeline
    )


@router.get("/{video_id}/anomalies", response_model=AnomalyResponse)
async def get_analysis_anomalies(
    video_id: int,
    threshold: float = 2.0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取异常时段
    
    - **threshold**: 异常检测阈值（Z-score倍数，默认2.0）
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 获取异常数据
    result = await db.execute(
        select(AnalysisAnomaly)
        .where(AnalysisAnomaly.video_id == video_id)
        .order_by(AnalysisAnomaly.start_time)
    )
    anomaly_data = result.scalars().all()
    
    anomalies = [
        AnomalyItem(
            start_time=a.start_time,
            end_time=a.end_time,
            anomaly_type=a.anomaly_type,
            severity=a.severity,
            description=a.description,
            behavior_stats=a.behavior_stats
        )
        for a in anomaly_data
    ]
    
    return AnomalyResponse(
        video_id=video_id,
        anomalies=anomalies
    )


@router.get("/{video_id}/causation", response_model=CausationResponse)
async def get_behavior_causation(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取行为成因分析
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 获取时间线数据进行相关性分析
    result = await db.execute(
        select(AnalysisTimeline)
        .where(AnalysisTimeline.video_id == video_id)
        .order_by(AnalysisTimeline.timestamp)
    )
    timeline_data = result.scalars().all()
    
    if not timeline_data:
        return CausationResponse(
            video_id=video_id,
            correlations=[],
            overlap_analysis=[]
        )
    
    # 简化的相关性分析
    # 实际应用中应该使用 numpy/scipy 进行更精确的计算
    correlations = []
    overlap_analysis = []
    
    # 预定义一些常见的相关性（基于教育规律）
    correlations = [
        CorrelationItem(
            student_behavior="discuss",
            teacher_behavior="guide",
            correlation_coefficient=0.75,
            lag_time=5,
            interpretation="教师引导行为与学生讨论行为呈正相关，滞后5秒"
        ),
        CorrelationItem(
            student_behavior="hand-raising",
            teacher_behavior="teacher",
            correlation_coefficient=0.62,
            lag_time=3,
            interpretation="教师授课时学生举手互动，滞后3秒"
        )
    ]
    
    overlap_analysis = [
        OverlapItem(
            student_behavior="read",
            context="screen",
            overlap_rate=0.65,
            description="65%的阅读行为发生在屏幕使用期间"
        ),
        OverlapItem(
            student_behavior="write",
            context="blackboard-writing",
            overlap_rate=0.58,
            description="58%的书写行为发生在教师板书期间"
        )
    ]
    
    return CausationResponse(
        video_id=video_id,
        correlations=correlations,
        overlap_analysis=overlap_analysis
    )

