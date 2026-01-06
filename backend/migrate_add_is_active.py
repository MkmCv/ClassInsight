"""
数据库迁移脚本：为用户表添加 is_active 字段
"""
import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine, AsyncSessionLocal


async def migrate():
    """执行迁移"""
    async with AsyncSessionLocal() as session:
        try:
            # SQLite 检查字段是否存在
            result = await session.execute(text("PRAGMA table_info(users)"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]  # 第二列是列名
            
            if 'is_active' in column_names:
                print("✅ is_active 字段已存在，无需迁移")
                return
            
            # 添加 is_active 字段
            print("🔄 正在添加 is_active 字段...")
            await session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN is_active INTEGER DEFAULT 1 NOT NULL
            """))
            
            await session.commit()
            print("✅ 迁移完成！所有用户已设置为启用状态（默认值）")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 迁移失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("数据库迁移：添加 is_active 字段")
    print("=" * 50)
    asyncio.run(migrate())
