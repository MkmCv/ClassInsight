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
    CausationResponse, CorrelationItem, OverlapItem,
    TeachingModeResponse, TeachingModeItem, ModeTransitionItem, ModeTimelinePoint
)
from ....services.behavior_analyzer import (
    analyze_behavior_correlations,
    analyze_behavior_overlap,
    analyze_teaching_modes
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
    
    # 获取原始和分类后的数据
    raw_behavior_summary = summary_data.get("behavior_summary", {})
    classified_data = summary_data.get("_classified", {})
    
    # 构建响应 - 同时包含原始和分类后的数据，确保兼容性
    behavior_summary = {}
    teacher_behavior = {}
    
    # 首先添加原始数据（用于兼容性和关键指标计算）
    for behavior, data in raw_behavior_summary.items():
        if behavior == "_classified":  # 跳过分类数据标记
            continue
        if isinstance(data, dict):
            # 检查是否是原始类别数据（不是嵌套的分类数据）
            if "type" not in data or data.get("type") == "raw":
                if behavior in STUDENT_BEHAVIORS:
                    behavior_summary[behavior] = BehaviorStat(**data)
                elif behavior in TEACHER_BEHAVIORS:
                    teacher_behavior[behavior] = BehaviorStat(**data)
    
    # 如果有分类后的数据，添加或覆盖（优先显示分类后的数据）
    if classified_data:
        student_behaviors = classified_data.get("student_behaviors", {})
        teacher_behaviors = classified_data.get("teacher_behaviors", {})
        
        for behavior, data in student_behaviors.items():
            behavior_summary[behavior] = BehaviorStat(**data)
        
        for behavior, data in teacher_behaviors.items():
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
      注意：处理管线当前仅写入 window_size=10；若需 60s 应对数据二次聚合或扩展写入。
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 验证 window 参数
    if window not in [10, 60]:
        window = 10
    
    # 按库中已存储的 window_size 过滤（与 process_video_task 写入一致）
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
    
    timeline = []
    for t in timeline_data:
        behavior_counts = t.behavior_counts or {}
        
        # 处理行为数据：保持原有格式，移除内部标记字段
        if isinstance(behavior_counts, dict):
            # 移除内部标记字段（_raw, _classified），保留实际行为数据
            behaviors = {
                k: v for k, v in behavior_counts.items() 
                if k not in ["_raw", "_classified", "raw_behavior_counts", "student_behaviors", "teacher_behaviors"]
            }
            # 如果有分类后的数据，也包含进来（已经在上面的字典中）
        else:
            behaviors = behavior_counts
        
        timeline.append(TimelinePoint(
            timestamp=t.timestamp,
            behaviors=behaviors
        ))
    
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
    
    # 转换为分析服务需要的格式
    timeline_list = [
        {
            "timestamp": t.timestamp,
            "behavior_counts": t.behavior_counts
        }
        for t in timeline_data
    ]
    
    # 使用真实统计方法计算相关性
    correlation_results = analyze_behavior_correlations(timeline_list, window_size=10)
    
    # 转换为响应格式
    correlations = [
        CorrelationItem(
            student_behavior=r["student_behavior"],
            teacher_behavior=r["teacher_behavior"],
            correlation_coefficient=r["correlation_coefficient"],
            lag_time=r["lag_time"],
            interpretation=r["interpretation"]
        )
        for r in correlation_results
    ]
    
    # 分析行为重叠
    overlap_results = analyze_behavior_overlap(timeline_list)
    overlap_analysis = [
        OverlapItem(
            student_behavior=r["student_behavior"],
            context=r["context"],
            overlap_rate=r["overlap_rate"],
            description=r["description"]
        )
        for r in overlap_results
    ]
    
    return CausationResponse(
        video_id=video_id,
        correlations=correlations,
        overlap_analysis=overlap_analysis
    )


@router.get("/{video_id}/teaching-modes", response_model=TeachingModeResponse)
async def get_teaching_modes(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取教学模式分析
    自动识别教学模式（讲授/互动/练习等），分析模式占比和转换
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 获取时间线数据
    result = await db.execute(
        select(AnalysisTimeline)
        .where(
            and_(
                AnalysisTimeline.video_id == video_id,
                AnalysisTimeline.window_size == 10
            )
        )
        .order_by(AnalysisTimeline.timestamp)
    )
    timeline_data = result.scalars().all()
    
    if not timeline_data:
        return TeachingModeResponse(
            video_id=video_id,
            modes=[],
            mode_distribution={},
            mode_percentages={},
            transitions=[],
            mode_timeline=[],
            total_windows=0
        )
    
    # 转换为分析服务需要的格式
    timeline_list = [
        {
            "timestamp": t.timestamp,
            "behavior_counts": t.behavior_counts
        }
        for t in timeline_data
    ]
    
    # 分析教学模式
    mode_analysis = analyze_teaching_modes(timeline_list)
    
    # 构建模式转换列表
    transition_counts = mode_analysis.get("transition_counts", {})
    transitions = [
        ModeTransitionItem(
            from_mode=from_mode,
            to_mode=to_mode,
            count=count,
            timestamp=None  # 可以添加示例时间戳
        )
        for (from_mode, to_mode), count in transition_counts.items()
    ]
    
    # 构建模式时间线
    mode_timeline = [
        ModeTimelinePoint(
            timestamp=item["timestamp"],
            mode=item["mode"]
        )
        for item in mode_analysis.get("mode_timeline", [])
    ]
    
    return TeachingModeResponse(
        video_id=video_id,
        modes=mode_analysis.get("modes", []),
        mode_distribution=mode_analysis.get("mode_distribution", {}),
        mode_percentages=mode_analysis.get("mode_percentages", {}),
        transitions=transitions,
        mode_timeline=mode_timeline,
        total_windows=mode_analysis.get("total_windows", 0)
    )














