"""
分析结果相关的 Pydantic 模式
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class BehaviorStat(BaseModel):
    """单个行为的统计数据"""
    count: int = Field(..., description="发生次数")
    total_duration: float = Field(..., description="总时长（秒）")
    percentage: float = Field(..., description="占比（%）")


class AnalysisSummaryResponse(BaseModel):
    """整课行为统计汇总响应"""
    video_id: int
    duration: float = Field(..., description="视频时长（秒）")
    total_frames: int = Field(..., description="总帧数")
    behavior_summary: Dict[str, BehaviorStat] = Field(..., description="学生行为统计")
    teacher_behavior: Dict[str, BehaviorStat] = Field(..., description="教师行为统计")


class TimelinePoint(BaseModel):
    """时间线单个数据点"""
    timestamp: int = Field(..., description="时间戳（秒）")
    behaviors: Dict[str, int] = Field(..., description="该时间窗口内各行为的数量")


class TimelineResponse(BaseModel):
    """时间序列数据响应"""
    video_id: int
    window_size: int = Field(..., description="时间窗口大小（秒）")
    timeline: List[TimelinePoint]


class AnomalyItem(BaseModel):
    """异常事件项"""
    start_time: int = Field(..., description="开始时间（秒）")
    end_time: int = Field(..., description="结束时间（秒）")
    type: str = Field(..., alias="anomaly_type", description="异常类型")
    severity: str = Field(..., description="严重程度: low, medium, high")
    description: str = Field(..., description="异常描述")
    behavior_stats: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class AnomalyResponse(BaseModel):
    """异常时段响应"""
    video_id: int
    anomalies: List[AnomalyItem]


class CorrelationItem(BaseModel):
    """相关性分析项"""
    student_behavior: str
    teacher_behavior: str
    correlation_coefficient: float = Field(..., description="Pearson相关系数")
    lag_time: int = Field(..., description="滞后时间（秒）")
    interpretation: str


class OverlapItem(BaseModel):
    """重叠分析项"""
    student_behavior: str
    context: str
    overlap_rate: float
    description: str


class CausationResponse(BaseModel):
    """行为成因分析响应"""
    video_id: int
    correlations: List[CorrelationItem]
    overlap_analysis: List[OverlapItem]

