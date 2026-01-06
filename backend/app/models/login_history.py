"""
登录历史记录模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..core.database import Base


class LoginHistory(Base):
    """登录历史记录表"""
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)  # 浏览器信息
    login_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = Column(String(20), default="success", nullable=False)  # success, failed
    failure_reason = Column(String(200), nullable=True)  # 失败原因
    
    # 关联关系
    user = relationship("User", backref="login_history")
    
    def __repr__(self):
        return f"<LoginHistory(user_id={self.user_id}, username='{self.username}', status='{self.status}')>"








