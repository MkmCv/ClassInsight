"""
数据库连接和会话管理
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from .config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# SQLite：默认可能未启用外键约束（会影响 CASCADE / ondelete）
if str(settings.DATABASE_URL).startswith("sqlite"):
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[no-redef]
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            # 避免并发写入时的“database is locked”概率（单位 ms）
            cursor.execute("PRAGMA busy_timeout=5000")
        finally:
            cursor.close()

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# 声明基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库（创建所有表）"""
    # 确保所有模型已加载到 Base.metadata（否则 create_all 可能为空）
    from .. import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()





















