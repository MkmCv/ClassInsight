"""
用户相关的 Pydantic 模式
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")


class UserCreate(UserBase):
    """用户注册请求"""
    password: str = Field(..., min_length=8, description="密码，至少8位")
    role: str = Field(default="teacher", description="角色: teacher | admin")
    unit: Optional[str] = Field(None, max_length=100, description="单位")
    class_name: Optional[str] = Field(None, max_length=50, description="班级")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    """用户信息更新"""
    email: Optional[EmailStr] = None
    unit: Optional[str] = None
    class_name: Optional[str] = None


class PasswordChange(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码，至少8位")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    role: str
    unit: Optional[str] = None
    class_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录Token响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

