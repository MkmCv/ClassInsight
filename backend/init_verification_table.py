"""
初始化验证码表
确保所有模型表都已创建
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import init_db
from app.models import User, Video, AnalysisTimeline, AnalysisSummary, AnalysisAnomaly, Schedule, VerificationCode

async def main():
    print("=" * 50)
    print("🔄 正在初始化数据库表...")
    print("=" * 50)
    
    try:
        await init_db()
        print("\n✅ 数据库表初始化完成！")
        print("\n已创建的表：")
        print("  - users")
        print("  - videos")
        print("  - analysis_timelines")
        print("  - analysis_summaries")
        print("  - analysis_anomalies")
        print("  - schedules")
        print("  - verification_codes ✅")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

