"""
分析结果模型
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    Text,
    JSON,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from ..core.database import Base


class AnalysisTimeline(Base):
    """时间序列分析数据表 - 存储每个时间窗口的行为统计"""
    __tablename__ = "analysis_timeline"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 时间信息：timestamp 为时间窗起点（秒），与 video_processor 中 window_key 一致
    timestamp = Column(Integer, nullable=False)
    window_size = Column(Integer, default=10)  # 窗长（秒）；当前写入多为 10
    
    # 行为统计（JSON格式存储每个类别的数量）
    # 格式: {"discuss": 3, "hand-raising": 1, "read": 15, ...}
    behavior_counts = Column(JSON, nullable=False)
    
    # 检测框原始数据（可选，用于回放）
    # 格式: [{"category": "teacher", "bbox": [x1,y1,x2,y2], "score": 0.95}, ...]
    detections = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        # 常用查询：按 video_id + 时间范围拉取时间线
        Index("idx_analysis_timeline_video_timestamp", "video_id", "timestamp"),
        # 防止同一窗口重复写入（对新建数据库生效；现有库不强制，但可避免未来重复）
        UniqueConstraint(
            "video_id",
            "timestamp",
            "window_size",
            name="uq_analysis_timeline_video_timestamp_window",
        ),
        CheckConstraint("timestamp >= 0", name="ck_analysis_timeline_timestamp_nonneg"),
        CheckConstraint("window_size > 0", name="ck_analysis_timeline_window_size_pos"),
    )

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
    
    __table_args__ = (
        # 指标范围约束（对新建数据库生效）
        CheckConstraint(
            "(interaction_rate IS NULL) OR (interaction_rate >= 0 AND interaction_rate <= 1)",
            name="ck_analysis_summary_interaction_rate_0_1",
        ),
        CheckConstraint(
            "(attention_rate IS NULL) OR (attention_rate >= 0 AND attention_rate <= 1)",
            name="ck_analysis_summary_attention_rate_0_1",
        ),
        CheckConstraint(
            "(engagement_score IS NULL) OR (engagement_score >= 0 AND engagement_score <= 1)",
            name="ck_analysis_summary_engagement_score_0_1",
        ),
    )

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
    
    __table_args__ = (
        Index("idx_analysis_anomalies_video_time", "video_id", "start_time", "end_time"),
        CheckConstraint("start_time >= 0", name="ck_analysis_anomalies_start_time_nonneg"),
        CheckConstraint("end_time >= 0", name="ck_analysis_anomalies_end_time_nonneg"),
        CheckConstraint("end_time > start_time", name="ck_analysis_anomalies_time_range"),
        CheckConstraint(
            "severity IN ('low','medium','high')",
            name="ck_analysis_anomalies_severity_enum",
        ),
    )

    # 关联关系
    video = relationship("Video", back_populates="anomalies")
    
    def __repr__(self):
        return f"<AnalysisAnomaly(video_id={self.video_id}, type='{self.anomaly_type}')>"





















