"""
验证码模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, CheckConstraint
from ..core.database import Base


class VerificationCode(Base):
    """验证码表"""
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), index=True, nullable=False)
    code = Column(String(6), nullable=False)  # 6位数字验证码
    purpose = Column(String(20), nullable=False)  # reset_password, register
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        # 常用查询：按 email + purpose 查最新可用验证码
        Index("idx_verification_email_purpose_created", "email", "purpose", "created_at"),
        CheckConstraint("length(code) = 6", name="ck_verification_code_len_6"),
    )
    
    def __repr__(self):
        return f"<VerificationCode(email='{self.email}', purpose='{self.purpose}')>"

















