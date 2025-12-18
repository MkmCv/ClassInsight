"""
启动脚本 - 用于快速启动后端服务
"""
import os
import sys
from pathlib import Path

# 确保在正确的目录
os.chdir(Path(__file__).parent)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """主启动函数"""
    import uvicorn
    from app.core.config import settings
    
    print("=" * 50)
    print("🎓 ClassInsight 课堂行为分析系统")
    print("=" * 50)
    print(f"📌 API 文档: http://localhost:8000/api/docs")
    print(f"📌 ReDoc 文档: http://localhost:8000/api/redoc")
    print(f"📌 健康检查: http://localhost:8000/health")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()

