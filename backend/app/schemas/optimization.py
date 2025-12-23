"""
教学优化相关的 Pydantic 模式
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """单条建议"""
    type: str = Field(..., description="建议类型: interaction, attention, rhythm, engagement")
    priority: str = Field(..., description="优先级: low, medium, high")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议详情")
    suggested_actions: List[str] = Field(..., description="建议行动列表")


class RecommendationResponse(BaseModel):
    """优化建议响应"""
    video_id: int
    recommendations: List[RecommendationItem]


class HighlightItem(BaseModel):
    """优秀课堂片段"""
    start_time: int = Field(..., description="开始时间（秒）")
    end_time: int = Field(..., description="结束时间（秒）")
    score: float = Field(..., ge=0, le=1, description="质量评分")
    reasons: List[str] = Field(..., description="被选为精彩片段的原因")
    thumbnail_url: Optional[str] = None


class HighlightResponse(BaseModel):
    """优秀片段响应"""
    video_id: int
    highlights: List[HighlightItem]


class RadarMetric(BaseModel):
    """雷达图单项指标"""
    value: float = Field(..., ge=0, le=100, description="得分（0-100）")
    description: str


class RadarResponse(BaseModel):
    """雷达图数据响应"""
    video_id: int
    metrics: Dict[str, RadarMetric] = Field(..., description="各维度得分")
    # 预期维度: interaction, attention, activity, guidance, multimedia


class CompareMetrics(BaseModel):
    """对比指标"""
    interaction_rate: float
    attention_rate: float
    engagement_score: float


class CompareItem(BaseModel):
    """对比项"""
    video_id: int
    lesson_date: Optional[str] = None
    metrics: CompareMetrics


class CompareTrends(BaseModel):
    """趋势分析"""
    interaction_rate: str = Field(..., description="increasing, decreasing, stable")
    attention_rate: str
    engagement_score: str


class CompareResponse(BaseModel):
    """跨课次对比响应"""
    comparison: List[CompareItem]
    trends: CompareTrends





