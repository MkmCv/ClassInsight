"""
ClassInsight Backend - 主应用入口

课堂行为分析系统后端服务
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# 添加项目路径到系统路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings, init_directories
from app.core.database import init_db, close_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 ClassInsight Backend 启动中...")
    
    # 初始化目录
    init_directories()
    
    # 初始化数据库
    await init_db()
    print("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时执行
    await close_db()
    print("👋 ClassInsight Backend 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🎓 ClassInsight 课堂行为分析系统 API

基于 vHeat 算法的智能课堂行为分析后端服务。

### 主要功能模块：

* **🔐 认证模块** - 用户注册、登录、Token管理
* **📤 视频管理** - 视频上传、处理状态查询、删除
* **📈 行为分析** - 整课统计、时间序列、异常检测
* **💡 教学优化** - 雷达图、改进建议、优秀片段

### 技术特点：

- 基于 FastAPI 的高性能异步框架
- YOLO-vHeat 多模型协同检测
- SQLAlchemy 异步 ORM
- JWT Token 认证
    """,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """API 根路径"""
    return {
        "message": "欢迎使用 ClassInsight API",
        "docs": "/api/docs",
        "version": settings.APP_VERSION
    }


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "message": str(exc) if settings.DEBUG else "请稍后重试"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )





