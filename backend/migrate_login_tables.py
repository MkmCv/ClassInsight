"""
创建登录相关表的迁移脚本
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.login_attempt import LoginAttempt
from app.models.login_history import LoginHistory
from app.core.config import settings


async def create_tables():
    """创建登录相关表"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # 创建表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 登录相关表创建成功！")
    print("   - login_attempts (登录尝试记录)")
    print("   - login_history (登录历史记录)")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())








