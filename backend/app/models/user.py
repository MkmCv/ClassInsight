"""
用户模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, CheckConstraint
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    TEACHER = "teacher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.TEACHER.value, nullable=False)
    unit = Column(String(100), nullable=True)  # 单位/学校
    class_name = Column(String(50), nullable=True)  # 班级
    is_active = Column(Integer, default=1, nullable=False)  # 1=启用, 0=禁用
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("is_active IN (0, 1)", name="ck_users_is_active_0_1"),
        CheckConstraint(
            "role IN ('teacher','admin','super_admin')",
            name="ck_users_role_enum",
        ),
    )
    
    # 关联关系
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"





