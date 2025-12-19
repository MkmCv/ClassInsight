"""
分析结果模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base


class AnalysisTimeline(Base):
    """时间序列分析数据表 - 存储每个时间窗口的行为统计"""
    __tablename__ = "analysis_timeline"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 时间信息
    timestamp = Column(Integer, nullable=False)  # 时间戳（秒）
    window_size = Column(Integer, default=10)    # 窗口大小（秒）
    
    # 行为统计（JSON格式存储每个类别的数量）
    # 格式: {"discuss": 3, "hand-raising": 1, "read": 15, ...}
    behavior_counts = Column(JSON, nullable=False)
    
    # 检测框原始数据（可选，用于回放）
    # 格式: [{"category": "teacher", "bbox": [x1,y1,x2,y2], "score": 0.95}, ...]
    detections = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联关系
    video = relationship("Video", back_populates="timeline")
    
    def __repr__(self):
        return f"<AnalysisTimeline(video_id={self.video_id}, timestamp={self.timestamp})>"


class AnalysisSummary(Base):
    """整课分析汇总表 - 存储聚合后的统计数据"""
    __tablename__ = "analysis_summary"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # 汇总数据（JSON格式）
    # 格式: {
    #   "behavior_summary": {
    #     "discuss": {"count": 45, "total_duration": 1200, "percentage": 33.3},
    #     ...
    #   },
    #   "teacher_behavior": {
    #     "teacher": {...},
    #     ...
    #   }
    # }
    summary_json = Column(JSON, nullable=False)
    
    # 计算指标
    total_detections = Column(Integer, default=0)
    interaction_rate = Column(Float, nullable=True)  # 互动率
    attention_rate = Column(Float, nullable=True)    # 专注度
    engagement_score = Column(Float, nullable=True)  # 参与度评分
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    video = relationship("Video", back_populates="summary")
    
    def __repr__(self):
        return f"<AnalysisSummary(video_id={self.video_id})>"


class AnalysisAnomaly(Base):
    """异常事件表 - 存储检测到的异常时段"""
    __tablename__ = "analysis_anomalies"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 时间范围
    start_time = Column(Integer, nullable=False)  # 秒
    end_time = Column(Integer, nullable=False)    # 秒
    
    # 异常信息
    anomaly_type = Column(String(50), nullable=False)  # 如 "high_bowhead_rate"
    severity = Column(String(20), nullable=False)      # low, medium, high
    description = Column(Text, nullable=False)
    
    # 相关统计数据
    behavior_stats = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关联关系
    video = relationship("Video", back_populates="anomalies")
    
    def __repr__(self):
        return f"<AnalysisAnomaly(video_id={self.video_id}, type='{self.anomaly_type}')>"


