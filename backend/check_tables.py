"""
检查数据库表是否存在
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal


async def check_tables():
    """检查所有表是否存在"""
    async with AsyncSessionLocal() as session:
        try:
            # SQLite 查询所有表名
            result = await session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            print("=" * 50)
            print("📊 数据库表检查")
            print("=" * 50)
            print(f"\n已存在的表 ({len(tables)} 个):")
            for table in tables:
                print(f"  ✅ {table}")
            
            # 检查必需的表
            required_tables = [
                "users",
                "videos", 
                "analysis_timelines",
                "analysis_summaries",
                "analysis_anomalies",
                "schedules",
                "verification_codes"
            ]
            
            print(f"\n必需的表检查:")
            missing = []
            for table in required_tables:
                if table in tables:
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table} - 缺失！")
                    missing.append(table)
            
            if missing:
                print(f"\n⚠️  缺少 {len(missing)} 个表，请运行初始化脚本:")
                print(f"   python init_verification_table.py")
                return False
            else:
                print(f"\n✅ 所有必需的表都存在！")
                return True
                
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    asyncio.run(check_tables())









