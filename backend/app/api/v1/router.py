"""
API v1 路由聚合
"""
from fastapi import APIRouter
from .endpoints import auth, videos, analysis, optimization, dashboard, admin

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["首页"])
api_router.include_router(videos.router, prefix="/videos", tags=["视频管理"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["行为分析"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["教学优化"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])


