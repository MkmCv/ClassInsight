"""
课程表模型
"""
from datetime import datetime, time
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Time,
    Date,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
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
    
    __table_args__ = (
        # 常用查询：查某教师某天课表
        Index("idx_schedules_user_day", "user_id", "day_of_week"),
        # 防止完全重复的课表条目
        UniqueConstraint(
            "user_id",
            "day_of_week",
            "start_time",
            "end_time",
            "course_name",
            "class_name",
            name="uq_schedules_user_time_course_class",
        ),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_schedules_day_of_week_0_6"),
        # SQLite/PG 都支持对 TIME 做比较（对新建数据库生效）
        CheckConstraint("end_time > start_time", name="ck_schedules_time_range"),
    )

    # 关联关系
    user = relationship("User", back_populates="schedules")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, course='{self.course_name}', class='{self.class_name}')>"





















