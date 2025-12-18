"""
课程表模型
"""
from datetime import datetime, time
from sqlalchemy import Column, Integer, String, DateTime, Time, Date, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base


class Schedule(Base):
    """课程表"""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 课程信息
    course_name = Column(String(50), nullable=False)
    class_name = Column(String(50), nullable=False)
    
    # 时间安排
    day_of_week = Column(Integer, nullable=False)  # 0-6 表示周一到周日
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    user = relationship("User", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, course='{self.course_name}', class='{self.class_name}')>"

