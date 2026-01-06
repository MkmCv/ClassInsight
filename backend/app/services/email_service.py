"""
邮件服务 - 用于发送验证码等
"""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..core.config import settings
from ..models.verification import VerificationCode


def generate_verification_code(length: int = 6) -> str:
    """生成数字验证码"""
    return ''.join(random.choices(string.digits, k=length))


async def create_verification_code(
    db: AsyncSession,
    email: str,
    purpose: str = "reset_password"
) -> str:
    """创建验证码并存入数据库"""
    # 生成验证码
    code = generate_verification_code()
    
    # 计算过期时间
    expires_at = datetime.utcnow() + timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
    
    # 将之前未使用的验证码标记为已使用
    result = await db.execute(
        select(VerificationCode).where(and_(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose,
            VerificationCode.used == False
        ))
    )
    old_codes = result.scalars().all()
    for old_code in old_codes:
        old_code.used = True
    
    # 创建新验证码
    verification = VerificationCode(
        email=email,
        code=code,
        purpose=purpose,
        expires_at=expires_at,
        used=False
    )
    
    db.add(verification)
    await db.commit()
    
    return code


async def verify_code(
    db: AsyncSession,
    email: str,
    code: str,
    purpose: str = "reset_password"
) -> Tuple[bool, str]:
    """验证验证码"""
    result = await db.execute(
        select(VerificationCode).where(and_(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.purpose == purpose,
            VerificationCode.used == False
        ))
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        return False, "验证码无效"
    
    # 检查是否过期
    if datetime.utcnow() > verification.expires_at:
        return False, "验证码已过期"
    
    # 标记为已使用
    verification.used = True
    await db.commit()
    
    return True, "验证成功"


def send_email(to_email: str, subject: str, html_content: str) -> Tuple[bool, str]:
    """
    发送邮件
    
    Returns:
        (success, message)
    """
    # 检查配置
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        # 开发模式：打印到控制台
        print("=" * 50)
        print(f"📧 [开发模式] 邮件发送模拟")
        print(f"收件人: {to_email}")
        print(f"主题: {subject}")
        print(f"内容: {html_content}")
        print("=" * 50)
        return True, "开发模式：验证码已打印到控制台"
    
    try:
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg['To'] = to_email
        
        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 发送邮件
        if settings.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
        
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, [to_email], msg.as_string())
        server.quit()
        
        return True, "邮件发送成功"
        
    except smtplib.SMTPAuthenticationError:
        return False, "邮箱认证失败，请检查SMTP配置"
    except smtplib.SMTPException as e:
        return False, f"邮件发送失败: {str(e)}"
    except Exception as e:
        return False, f"发送错误: {str(e)}"


def send_verification_email(to_email: str, code: str) -> Tuple[bool, str]:
    """发送验证码邮件"""
    subject = f"【ClassInsight】密码重置验证码: {code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
            <h1 style="color: white; margin: 0;">🎓 ClassInsight</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">课堂行为智能分析系统</p>
        </div>
        
        <div style="padding: 30px; background: #f9fafb; border-radius: 0 0 10px 10px;">
            <h2 style="color: #374151;">密码重置验证码</h2>
            <p style="color: #6b7280;">您正在重置 ClassInsight 账号密码，验证码为：</p>
            
            <div style="background: white; border: 2px dashed #667eea; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0;">
                <span style="font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 8px;">{code}</span>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">
                ⏰ 验证码有效期 <strong>{settings.VERIFICATION_CODE_EXPIRE_MINUTES} 分钟</strong>，请尽快使用。<br>
                ⚠️ 如非本人操作，请忽略此邮件。
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
            <p>© 2025 ClassInsight - 基于 VHEAT 的课堂行为分析系统</p>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, subject, html_content)

















