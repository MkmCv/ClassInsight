"""
认证模块 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field

from ....core.database import get_db
from ....core.config import settings
from ....core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from ....models.user import User
from ....schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, PasswordChange
from ....services.email_service import create_verification_code, verify_code, send_verification_email
from ....services.login_service import (
    check_login_attempts,
    record_login_attempt,
    record_login_history,
    get_login_attempt_info,
    get_client_ip
)
from ...deps import get_current_user

router = APIRouter()


# ==================== 忘记密码相关Schema ====================
class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr = Field(..., description="注册邮箱")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    email: EmailStr = Field(..., description="注册邮箱")
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")
    new_password: str = Field(..., min_length=8, description="新密码，至少8位")


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册
    """
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=user_data.role,
        unit=user_data.unit,
        class_name=user_data.class_name
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "user_id": user.id,
        "username": user.username,
        "message": "注册成功"
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录 (OAuth2 兼容)
    支持登录失败次数限制、用户状态检查
    """
    try:
        ip_address = get_client_ip(request) if request else "unknown"
    except:
        ip_address = "unknown"
    
    # 检查登录尝试次数
    allowed, error_msg = await check_login_attempts(db, form_data.username, ip_address)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查找用户
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    # 验证密码
    if not user or not verify_password(form_data.password, user.password_hash):
        await record_login_attempt(db, form_data.username, ip_address, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户状态
    if user.is_active == 0:
        await record_login_attempt(db, form_data.username, ip_address, success=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用，请联系管理员",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 登录成功
    await record_login_attempt(db, form_data.username, ip_address, success=True)
    
    # 创建 tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录 (JSON 格式)
    支持登录失败次数限制、用户状态检查、登录历史记录
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 1. 检查登录尝试次数（防止暴力破解）
    allowed, error_msg = await check_login_attempts(db, user_data.username, ip_address)
    if not allowed:
        await record_login_history(
            db=db,
            user_id=0,
            username=user_data.username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed",
            failure_reason=error_msg
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )
    
    # 2. 查找用户
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()
    
    # 3. 验证密码
    if not user or not verify_password(user_data.password, user.password_hash):
        # 记录失败尝试
        await record_login_attempt(db, user_data.username, ip_address, success=False)
        await record_login_history(
            db=db,
            user_id=0,
            username=user_data.username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed",
            failure_reason="用户名或密码错误"
        )
        
        # 获取失败次数信息
        attempt_info = await get_login_attempt_info(db, user_data.username, ip_address)
        remaining = attempt_info["remaining_attempts"]
        
        error_detail = f"用户名或密码错误"
        if remaining > 0:
            error_detail += f"，剩余尝试次数：{remaining}"
        else:
            error_detail += f"，账户已被锁定{settings.LOGIN_LOCKOUT_MINUTES}分钟"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail
        )
    
    # 4. 检查用户状态（是否被禁用）
    if user.is_active == 0:
        await record_login_attempt(db, user_data.username, ip_address, success=False)
        await record_login_history(
            db=db,
            user_id=user.id,
            username=user_data.username,
            ip_address=ip_address,
            user_agent=user_agent,
            status="failed",
            failure_reason="账户已被禁用"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用，请联系管理员"
        )
    
    # 5. 登录成功
    # 清除失败记录
    await record_login_attempt(db, user_data.username, ip_address, success=True)
    
    # 记录登录历史
    await record_login_history(
        db=db,
        user_id=user.id,
        username=user_data.username,
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )
    
    # 创建 tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    """
    return UserResponse.model_validate(current_user)


@router.put("/password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码
    """
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "密码修改成功"}


# ==================== 忘记密码功能 ====================

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    忘记密码 - 发送验证码到邮箱
    """
    try:
        # 检查邮箱是否已注册
        result = await db.execute(select(User).where(User.email == request.email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该邮箱未注册"
            )
        
        # 生成验证码
        try:
            code = await create_verification_code(db, request.email, "reset_password")
        except Exception as e:
            # 如果创建验证码失败，可能是表不存在
            import traceback
            print(f"❌ 创建验证码失败: {e}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"验证码生成失败: {str(e)}"
            )
        
        # 发送邮件
        success, message = send_verification_email(request.email, code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        return {
            "message": "验证码已发送到您的邮箱",
            "email": request.email,
            "expires_in_minutes": 10
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ 忘记密码功能异常: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误: {str(e)}" if settings.DEBUG else "服务器内部错误"
        )


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    重置密码 - 验证验证码并设置新密码
    """
    # 验证验证码
    valid, message = await verify_code(db, request.email, request.code, "reset_password")
    
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # 查找用户
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(request.new_password)
    await db.commit()
    
    return {"message": "密码重置成功，请使用新密码登录"}


# ==================== 登录尝试信息 ====================

@router.get("/login/attempt-info")
async def get_login_attempt_info_endpoint(
    username: str = Query(..., description="用户名"),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取登录尝试信息（用于前端显示剩余尝试次数等）
    """
    ip_address = get_client_ip(request) if request else "unknown"
    info = await get_login_attempt_info(db, username, ip_address)
    return info


# ==================== 登录历史 ====================

@router.get("/login/history")
async def get_login_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="返回记录数")
):
    """
    获取当前用户的登录历史
    """
    from sqlalchemy import desc
    from ....models.login_history import LoginHistory
    
    result = await db.execute(
        select(LoginHistory)
        .where(LoginHistory.user_id == current_user.id)
        .order_by(desc(LoginHistory.login_time))
        .limit(limit)
    )
    histories = result.scalars().all()
    
    return [
        {
            "id": h.id,
            "ip_address": h.ip_address,
            "user_agent": h.user_agent,
            "login_time": h.login_time.isoformat(),
            "status": h.status,
            "failure_reason": h.failure_reason
        }
        for h in histories
    ]


