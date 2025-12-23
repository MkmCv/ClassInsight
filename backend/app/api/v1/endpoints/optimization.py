"""
教学优化 API 路由
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ....core.database import get_db
from ....models.user import User
from ....models.video import Video, VideoStatus
from ....models.analysis import AnalysisSummary
from ....schemas.optimization import (
    RecommendationResponse, RecommendationItem,
    HighlightResponse, HighlightItem,
    RadarResponse, RadarMetric,
    CompareResponse, CompareItem, CompareMetrics, CompareTrends
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


@router.get("/{video_id}/radar", response_model=RadarResponse)
async def get_radar_chart_data(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取教学能力雷达图数据
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 获取分析汇总
    result = await db.execute(
        select(AnalysisSummary).where(AnalysisSummary.video_id == video_id)
    )
    summary = result.scalar_one_or_none()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析数据不存在"
        )
    
    # 计算各维度得分
    interaction_rate = (summary.interaction_rate or 0) * 100
    attention_rate = (summary.attention_rate or 0) * 100
    
    # 从汇总数据中提取更多指标
    summary_data = summary.summary_json or {}
    behavior_summary = summary_data.get("behavior_summary", {})
    
    # 活跃度：基于举手频率
    hand_raising = behavior_summary.get("hand-raising", {})
    activity_score = min(100, (hand_raising.get("count", 0) / 10) * 100)
    
    # 教师引导：guide 行为占比
    guide_data = behavior_summary.get("guide", {})
    guidance_score = min(100, guide_data.get("percentage", 0) * 3)
    
    # 多媒体使用：screen 使用时长占比
    screen_data = behavior_summary.get("screen", {})
    multimedia_score = min(100, screen_data.get("percentage", 0) * 2)
    
    return RadarResponse(
        video_id=video_id,
        metrics={
            "interaction": RadarMetric(
                value=interaction_rate,
                description="课堂互动率"
            ),
            "attention": RadarMetric(
                value=attention_rate,
                description="学生专注度"
            ),
            "activity": RadarMetric(
                value=activity_score,
                description="课堂活跃度"
            ),
            "guidance": RadarMetric(
                value=guidance_score,
                description="教师引导力"
            ),
            "multimedia": RadarMetric(
                value=multimedia_score,
                description="多媒体运用"
            )
        }
    )


@router.get("/{video_id}/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取教学优化建议
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 获取分析汇总
    result = await db.execute(
        select(AnalysisSummary).where(AnalysisSummary.video_id == video_id)
    )
    summary = result.scalar_one_or_none()
    
    recommendations = []
    
    if summary:
        summary_data = summary.summary_json or {}
        behavior_summary = summary_data.get("behavior_summary", {})
        
        # 基于数据生成建议
        # 1. 检查讨论占比
        discuss_data = behavior_summary.get("discuss", {})
        discuss_pct = discuss_data.get("percentage", 0)
        if discuss_pct < 15:
            recommendations.append(RecommendationItem(
                type="interaction",
                priority="high",
                title="增加互动频次",
                description=f"讨论占比不足（当前{discuss_pct:.1f}%，建议≥15%），建议增加分组讨论环节",
                suggested_actions=[
                    "在课程中段（20-30分钟）增加小组讨论",
                    "设置讨论问题，引导学生互动",
                    "使用提问-回答形式增加课堂参与"
                ]
            ))
        
        # 2. 检查低头率
        bowhead_data = behavior_summary.get("BowHead", {})
        bowhead_pct = bowhead_data.get("percentage", 0)
        if bowhead_pct > 30:
            recommendations.append(RecommendationItem(
                type="attention",
                priority="high" if bowhead_pct > 40 else "medium",
                title="关注学生注意力",
                description=f"低头率偏高（{bowhead_pct:.1f}%），建议调整教学节奏",
                suggested_actions=[
                    "增加提问频次，吸引学生注意",
                    "使用多媒体素材丰富课堂内容",
                    "适当安排课间休息或活动"
                ]
            ))
        
        # 3. 检查举手参与
        handraising_data = behavior_summary.get("hand-raising", {})
        handraising_count = handraising_data.get("count", 0)
        if handraising_count < 5:
            recommendations.append(RecommendationItem(
                type="engagement",
                priority="medium",
                title="提升课堂参与度",
                description=f"学生举手次数较少（{handraising_count}次），建议鼓励更多主动参与",
                suggested_actions=[
                    "设置积分奖励机制鼓励发言",
                    "采用随机点名方式调动积极性",
                    "设计更多互动环节引导参与"
                ]
            ))
    
    # 如果没有生成建议，添加默认建议
    if not recommendations:
        recommendations.append(RecommendationItem(
            type="engagement",
            priority="low",
            title="保持良好教学状态",
            description="课堂整体表现良好，继续保持当前教学风格",
            suggested_actions=[
                "继续关注学生反馈",
                "尝试引入新的教学方法进行创新"
            ]
        ))
    
    return RecommendationResponse(
        video_id=video_id,
        recommendations=recommendations
    )


@router.get("/{video_id}/highlights", response_model=HighlightResponse)
async def get_highlights(
    video_id: int,
    min_score: float = 0.8,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取优秀课堂片段
    
    - **min_score**: 最低质量评分（0-1，默认0.8）
    """
    video = await verify_video_access(video_id, current_user, db)
    
    # 基于时间线数据识别高质量片段
    # 这里返回示例数据，实际应该基于分析结果
    highlights = [
        HighlightItem(
            start_time=600,
            end_time=900,
            score=0.92,
            reasons=[
                "互动占比高（35%）",
                "异常行为少（低头率<10%）",
                "教师引导与学生响应良好"
            ],
            thumbnail_url=f"/api/v1/videos/{video_id}/frames/600"
        ),
        HighlightItem(
            start_time=1800,
            end_time=2100,
            score=0.88,
            reasons=[
                "学生参与度高",
                "多人举手发言",
                "课堂气氛活跃"
            ],
            thumbnail_url=f"/api/v1/videos/{video_id}/frames/1800"
        )
    ]
    
    # 过滤低于阈值的片段
    highlights = [h for h in highlights if h.score >= min_score]
    
    return HighlightResponse(
        video_id=video_id,
        highlights=highlights
    )


@router.get("/compare", response_model=CompareResponse)
async def compare_videos(
    video_ids: str = Query(..., description="视频ID列表，逗号分隔"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    跨课次对比分析
    
    - **video_ids**: 视频ID列表，逗号分隔（如: 1,2,3）
    """
    # 解析视频ID
    try:
        ids = [int(id.strip()) for id in video_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频ID格式错误"
        )
    
    if len(ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="至少需要2个视频进行对比"
        )
    
    comparison = []
    
    for vid in ids:
        # 验证访问权限
        result = await db.execute(
            select(Video).where(
                and_(Video.id == vid, Video.user_id == current_user.id)
            )
        )
        video = result.scalar_one_or_none()
        
        if not video or video.status != VideoStatus.COMPLETED.value:
            continue
        
        # 获取分析数据
        result = await db.execute(
            select(AnalysisSummary).where(AnalysisSummary.video_id == vid)
        )
        summary = result.scalar_one_or_none()
        
        if summary:
            comparison.append(CompareItem(
                video_id=vid,
                lesson_date=video.lesson_date.isoformat() if video.lesson_date else None,
                metrics=CompareMetrics(
                    interaction_rate=summary.interaction_rate or 0,
                    attention_rate=summary.attention_rate or 0,
                    engagement_score=summary.engagement_score or 0
                )
            ))
    
    # 计算趋势
    if len(comparison) >= 2:
        def calc_trend(values):
            if len(values) < 2:
                return "stable"
            diff = values[-1] - values[0]
            if diff > 0.05:
                return "increasing"
            elif diff < -0.05:
                return "decreasing"
            return "stable"
        
        interaction_values = [c.metrics.interaction_rate for c in comparison]
        attention_values = [c.metrics.attention_rate for c in comparison]
        engagement_values = [c.metrics.engagement_score for c in comparison]
        
        trends = CompareTrends(
            interaction_rate=calc_trend(interaction_values),
            attention_rate=calc_trend(attention_values),
            engagement_score=calc_trend(engagement_values)
        )
    else:
        trends = CompareTrends(
            interaction_rate="stable",
            attention_rate="stable",
            engagement_score="stable"
        )
    
    return CompareResponse(
        comparison=comparison,
        trends=trends
    )





