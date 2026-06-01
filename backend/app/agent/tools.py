# -*- coding: utf-8 -*-
"""
Agent Tools 定义

定义 Agent 可调用的工具函数，用于获取课堂分析数据。
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import AsyncSessionLocal
from ..models.analysis import AnalysisSummary, AnalysisTimeline, AnalysisAnomaly

logger = logging.getLogger(__name__)


async def get_behavior_summary(video_id: int) -> Dict[str, Any]:
    """
    获取课堂行为汇总统计
    
    Args:
        video_id: 视频ID
        
    Returns:
        包含互动率、专注度、各行为统计的字典
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AnalysisSummary).where(AnalysisSummary.video_id == video_id)
        )
        summary = result.scalar_one_or_none()
        
        if summary:
            behavior_summary = summary.summary_json.get("behavior_summary", {}) if summary.summary_json else {}
            
            return {
                "video_id": video_id,
                "interaction_rate": round((summary.interaction_rate or 0) * 100, 1),
                "attention_rate": round((summary.attention_rate or 0) * 100, 1),
                "engagement_score": round((summary.engagement_score or 0) * 10, 1),
                "total_detections": summary.total_detections,
                "behaviors": {
                    name: {
                        "count": data.get("count", 0),
                        "duration_seconds": data.get("total_duration", 0),
                        "percentage": data.get("percentage", 0)
                    }
                    for name, data in behavior_summary.items()
                }
            }
        
        return {"error": f"未找到视频 {video_id} 的分析数据"}


async def get_behavior_timeline(video_id: int) -> List[Dict[str, Any]]:
    """
    获取课堂行为时间线数据（库中每行已是一段时间窗的聚合结果，此处按行读出并派生指标）
    
    Args:
        video_id: 视频ID
        
    Returns:
        时间线列表（与 AnalysisTimeline 行对应）
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AnalysisTimeline)
            .where(AnalysisTimeline.video_id == video_id)
            .order_by(AnalysisTimeline.timestamp)
        )
        timeline = result.scalars().all()
        
        if not timeline:
            return []
        
        # 提取时间线数据并分析趋势
        data = []
        for t in timeline:
            behaviors = t.behavior_counts or {}
            data.append({
                "timestamp": t.timestamp,
                "time_label": f"{t.timestamp // 60}分{t.timestamp % 60}秒",
                "behaviors": behaviors,
                # 计算该时段的互动强度
                "interaction_score": (
                    behaviors.get("guide", 0) * 30 +
                    behaviors.get("answer", 0) * 25 +
                    behaviors.get("On-stage interaction", 0) * 45
                ),
                # 计算该时段的注意力指标
                "attention_indicator": -behaviors.get("BowHead", 0) - behaviors.get("TurnHead", 0) * 0.5
            })
        
        return data


async def get_anomaly_events(video_id: int) -> List[Dict[str, Any]]:
    """
    获取课堂异常事件
    
    Args:
        video_id: 视频ID
        
    Returns:
        异常事件列表
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AnalysisAnomaly)
            .where(AnalysisAnomaly.video_id == video_id)
            .order_by(AnalysisAnomaly.start_time)
        )
        anomalies = result.scalars().all()
        
        return [{
            "type": a.anomaly_type,
            "severity": a.severity,
            "description": a.description,
            "start_time": a.start_time,
            "end_time": a.end_time,
            "time_range": f"{a.start_time // 60}分 - {a.end_time // 60}分",
            "details": a.behavior_stats
        } for a in anomalies]


def format_summary_for_prompt(summary: Dict[str, Any]) -> str:
    """
    将汇总数据格式化为 Prompt 可读格式
    """
    if "error" in summary:
        return f"⚠️ {summary['error']}"
    
    behaviors = summary.get("behaviors", {})
    
    # 学生行为统计
    student_behaviors = []
    for name in ["discuss", "hand-raising", "read", "write", "BowHead", "TurnHead", "answer", "On-stage interaction"]:
        if name in behaviors:
            b = behaviors[name]
            student_behaviors.append(f"  - {name}: {b['count']}次, {b['duration_seconds']}秒 ({b['percentage']:.1f}%)")
    
    # 教师行为统计
    teacher_behaviors = []
    for name in ["teacher", "guide", "blackboard-writing", "stand", "screen"]:
        if name in behaviors:
            b = behaviors[name]
            teacher_behaviors.append(f"  - {name}: {b['count']}次, {b['duration_seconds']}秒 ({b['percentage']:.1f}%)")
    
    return f"""【核心指标】
- 互动率: {summary['interaction_rate']}% {'✅' if summary['interaction_rate'] >= 15 else '⚠️ 偏低'}
- 专注度: {summary['attention_rate']}% {'✅' if summary['attention_rate'] >= 80 else '⚠️ 需关注'}
- 综合评分: {summary['engagement_score']}/10
- 总检测次数: {summary['total_detections']}

【学生行为统计】
{chr(10).join(student_behaviors) if student_behaviors else '  暂无数据'}

【教师行为统计】
{chr(10).join(teacher_behaviors) if teacher_behaviors else '  暂无数据'}
"""


def format_timeline_for_prompt(timeline: List[Dict[str, Any]]) -> str:
    """
    将时间线数据格式化为 Prompt 可读格式，提取关键趋势
    """
    if not timeline:
        return "暂无时间线数据"
    
    # 分析互动高峰和低谷
    interaction_scores = [(t["timestamp"], t["interaction_score"]) for t in timeline]
    if interaction_scores:
        max_interaction = max(interaction_scores, key=lambda x: x[1])
        low_interaction_periods = [t for t in timeline if t["interaction_score"] < 10]
    
    # 分析注意力变化
    attention_trend = []
    if len(timeline) >= 3:
        first_third = timeline[:len(timeline)//3]
        last_third = timeline[-len(timeline)//3:]
        
        first_bowhead = sum(t["behaviors"].get("BowHead", 0) for t in first_third)
        last_bowhead = sum(t["behaviors"].get("BowHead", 0) for t in last_third)
        
        if last_bowhead > first_bowhead * 1.5:
            attention_trend.append("⚠️ 注意力后期明显下降（低头行为增加50%以上）")
        elif last_bowhead < first_bowhead * 0.7:
            attention_trend.append("✅ 学生注意力保持良好或有所提升")
    
    result = []
    
    if max_interaction[1] > 0:
        result.append(f"📈 互动高峰: 第{max_interaction[0]//60}分钟（互动指数: {max_interaction[1]}）")
    
    if low_interaction_periods:
        periods = [f"{t['timestamp']//60}分" for t in low_interaction_periods[:3]]
        result.append(f"📉 低互动时段: {', '.join(periods)}")
    
    result.extend(attention_trend)
    
    return "\n".join(result) if result else "时间线数据正常，未发现明显异常模式"


def format_anomalies_for_prompt(anomalies: List[Dict[str, Any]]) -> str:
    """
    将异常事件格式化为 Prompt 可读格式
    """
    if not anomalies:
        return "✅ 未检测到明显异常，课堂状态良好"
    
    result = []
    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    
    for a in anomalies:
        emoji = severity_emoji.get(a["severity"], "⚪")
        result.append(f"{emoji} [{a['severity'].upper()}] {a['description']} ({a['time_range']})")
    
    return "\n".join(result)


