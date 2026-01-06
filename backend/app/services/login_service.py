"""
登录相关服务
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import Request, HTTPException, status

from ..models.login_attempt import LoginAttempt
from ..models.login_history import LoginHistory
from ..models.user import User
from ..core.config import settings


async def check_login_attempts(
    db: AsyncSession,
    username: str,
    ip_address: str = None
) -> tuple[bool, str]:
    """
    检查登录尝试次数，返回 (是否允许登录, 错误消息)
    """
    # 查找或创建登录尝试记录
    result = await db.execute(
        select(LoginAttempt).where(
            and_(
                LoginAttempt.username == username,
                LoginAttempt.ip_address == ip_address
            )
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        return True, ""
    
    # 检查是否被锁定
    if attempt.locked_until and attempt.locked_until > datetime.utcnow():
        remaining_minutes = int((attempt.locked_until - datetime.utcnow()).total_seconds() / 60)
        return False, f"账户已被锁定，请{remaining_minutes}分钟后再试"
    
    # 如果锁定时间已过，重置失败次数
    if attempt.locked_until and attempt.locked_until <= datetime.utcnow():
        attempt.failed_count = 0
        attempt.locked_until = None
        await db.commit()
    
    # 检查失败次数
    if attempt.failed_count >= settings.MAX_LOGIN_ATTEMPTS:
        # 锁定账户
        attempt.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        await db.commit()
        return False, f"登录失败次数过多，账户已被锁定{settings.LOGIN_LOCKOUT_MINUTES}分钟"
    
    return True, ""


async def record_login_attempt(
    db: AsyncSession,
    username: str,
    ip_address: str = None,
    success: bool = False
):
    """记录登录尝试"""
    # 查找或创建登录尝试记录
    result = await db.execute(
        select(LoginAttempt).where(
            and_(
                LoginAttempt.username == username,
                LoginAttempt.ip_address == ip_address
            )
        )
    )
    attempt = result.scalar_one_or_none()
    
    if success:
        # 登录成功，清除失败记录
        if attempt:
            await db.delete(attempt)
            await db.commit()
    else:
        # 登录失败，增加失败次数
        if not attempt:
            attempt = LoginAttempt(
                username=username,
                ip_address=ip_address,
                failed_count=1,
                last_attempt=datetime.utcnow()
            )
            db.add(attempt)
        else:
            attempt.failed_count += 1
            attempt.last_attempt = datetime.utcnow()
            
            # 如果达到最大失败次数，锁定账户
            if attempt.failed_count >= settings.MAX_LOGIN_ATTEMPTS:
                attempt.locked_until = datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        
        await db.commit()


async def record_login_history(
    db: AsyncSession,
    user_id: int,
    username: str,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "success",
    failure_reason: str = None
):
    """记录登录历史"""
    history = LoginHistory(
        user_id=user_id if status == "success" else None,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        failure_reason=failure_reason,
        login_time=datetime.utcnow()
    )
    db.add(history)
    await db.commit()


async def get_login_attempt_info(
    db: AsyncSession,
    username: str,
    ip_address: str = None
) -> dict:
    """获取登录尝试信息（用于前端显示）"""
    result = await db.execute(
        select(LoginAttempt).where(
            and_(
                LoginAttempt.username == username,
                LoginAttempt.ip_address == ip_address
            )
        )
    )
    attempt = result.scalar_one_or_none()
    
    if not attempt:
        return {
            "failed_count": 0,
            "remaining_attempts": settings.MAX_LOGIN_ATTEMPTS,
            "locked_until": None,
            "requires_captcha": False
        }
    
    remaining_attempts = max(0, settings.MAX_LOGIN_ATTEMPTS - attempt.failed_count)
    requires_captcha = attempt.failed_count >= settings.CAPTCHA_REQUIRED_AFTER
    
    return {
        "failed_count": attempt.failed_count,
        "remaining_attempts": remaining_attempts,
        "locked_until": attempt.locked_until.isoformat() if attempt.locked_until else None,
        "requires_captcha": requires_captcha
    }


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    if request.client:
        return request.client.host
    return "unknown"








