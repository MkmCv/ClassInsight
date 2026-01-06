"""
超级管理员 API 路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ....core.database import get_db
from ....core.config import settings
from ....models.user import User, UserRole
from ...deps import get_current_user

router = APIRouter()


async def get_super_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """验证当前用户是否为超级管理员"""
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以访问此功能"
        )
    return current_user


class SecurityConfigUpdate(BaseModel):
    """登录安全配置更新"""
    max_login_attempts: Optional[int] = None
    lockout_minutes: Optional[int] = None
    captcha_required_after: Optional[int] = None


@router.get("/login-security-config")
async def get_login_security_config(
    super_admin: User = Depends(get_super_admin_user)
):
    """
    获取登录安全配置（当前设置）
    """
    return {
        "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
        "lockout_minutes": settings.LOGIN_LOCKOUT_MINUTES,
        "captcha_required_after": settings.CAPTCHA_REQUIRED_AFTER,
        "note": "配置修改需要重启服务生效"
    }


@router.put("/login-security-config")
async def update_login_security_config(
    config: SecurityConfigUpdate,
    super_admin: User = Depends(get_super_admin_user)
):
    """
    更新登录安全配置
    注意：当前配置存储在代码中，此API仅用于展示。
    实际修改需要编辑 backend/app/core/config.py 并重启服务
    """
    # 返回当前配置和建议
    return {
        "message": "配置更新需要修改代码文件并重启服务",
        "current_config": {
            "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
            "lockout_minutes": settings.LOGIN_LOCKOUT_MINUTES,
            "captcha_required_after": settings.CAPTCHA_REQUIRED_AFTER,
        },
        "requested_config": config.model_dump(exclude_none=True),
        "instructions": {
            "file": "backend/app/core/config.py",
            "variables": [
                "MAX_LOGIN_ATTEMPTS",
                "LOGIN_LOCKOUT_MINUTES",
                "CAPTCHA_REQUIRED_AFTER"
            ],
            "note": "修改后需要重启后端服务"
        }
    }


@router.get("/model-info")
async def get_model_info(
    super_admin: User = Depends(get_super_admin_user)
):
    """
    获取模型信息
    """
    from pathlib import Path
    
    model_dir = Path(__file__).parent.parent.parent.parent.parent / "ml" / "weights"
    
    models = []
    if model_dir.exists():
        for model_file in model_dir.glob("*.pt"):
            models.append({
                "name": model_file.name,
                "path": str(model_file),
                "size": model_file.stat().st_size,
                "modified": model_file.stat().st_mtime
            })
    
    return {
        "model_directory": str(model_dir),
        "models": models,
        "current_config": {
            "model_weights_dir": str(settings.MODEL_WEIGHTS_DIR),
            "confidence_threshold": settings.MODEL_CONFIDENCE_THRESHOLD,
            "nms_iou_threshold": settings.MODEL_NMS_IOU_THRESHOLD,
        }
    }


@router.post("/model/update")
async def update_model(
    model_name: str = Body(..., description="模型文件名"),
    super_admin: User = Depends(get_super_admin_user)
):
    """
    更新模型（占位符，实际需要实现模型更新逻辑）
    """
    return {
        "message": "模型更新功能开发中",
        "model_name": model_name,
        "note": "此功能需要实现模型下载、验证和替换逻辑"
    }


@router.post("/model/activate")
async def activate_model(
    model_name: str = Body(..., description="要激活的模型文件名"),
    super_admin: User = Depends(get_super_admin_user)
):
    """
    激活最新模型（占位符，实际需要实现模型激活逻辑）
    """
    return {
        "message": "模型激活功能开发中",
        "model_name": model_name,
        "note": "此功能需要实现模型切换和验证逻辑"
    }

