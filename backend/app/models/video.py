"""
视频模型
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class VideoStatus(str, enum.Enum):
    """视频处理状态枚举"""
    UPLOADED = "uploaded"      # 已上传，等待处理
    PROCESSING = "processing"  # 正在处理
    COMPLETED = "completed"    # 处理完成
    FAILED = "failed"          # 处理失败


class Video(Base):
    """视频表"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 文件信息
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # 字节
    
    # 视频元数据
    duration = Column(Float, nullable=True)  # 秒
    fps = Column(Float, nullable=True)
    resolution = Column(String(20), nullable=True)  # 如 "1920x1080"
    total_frames = Column(Integer, nullable=True)
    
    # 课程信息
    class_name = Column(String(50), nullable=True)
    course_name = Column(String(50), nullable=True)
    lesson_date = Column(Date, nullable=True)
    
    # 处理状态
    status = Column(String(20), default=VideoStatus.UPLOADED.value, nullable=False, index=True)
    progress = Column(Float, default=0.0)  # 处理进度 0-1
    current_frame = Column(Integer, default=0)  # 当前处理帧
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)  # 处理完成时间
    
    # 关联关系
    user = relationship("User", back_populates="videos")
    timeline = relationship("AnalysisTimeline", back_populates="video", cascade="all, delete-orphan")
    summary = relationship("AnalysisSummary", back_populates="video", uselist=False, cascade="all, delete-orphan")
    anomalies = relationship("AnalysisAnomaly", back_populates="video", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Video(id={self.id}, filename='{self.filename}', status='{self.status}')>"

