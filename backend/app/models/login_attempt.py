"""
登录尝试记录模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index, UniqueConstraint
from ..core.database import Base


class LoginAttempt(Base):
    """登录尝试记录表（用于防暴力破解）"""
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6最长45字符
    failed_count = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)  # 锁定到期时间
    last_attempt = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 复合索引：用户名+IP
    __table_args__ = (
        Index('idx_username_ip', 'username', 'ip_address'),
        # 业务逻辑假设同一 username+ip 只有一条记录（防止出现重复行导致风控异常）
        UniqueConstraint('username', 'ip_address', name='uq_login_attempts_username_ip'),
    )
    
    def __repr__(self):
        return f"<LoginAttempt(username='{self.username}', failed_count={self.failed_count})>"








