"""
Mock 课表数据导入脚本

使用方法：
1. 确保后端服务已停止
2. 运行: python mock_schedules.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.models.schedule import Schedule


# Mock 课表数据
MOCK_SCHEDULES = [
    # 周一
    {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 0, "start_time": time(8, 0), "end_time": time(8, 45)},
    {"course_name": "数学", "class_name": "高一(2)班", "day_of_week": 0, "start_time": time(9, 0), "end_time": time(9, 45)},
    {"course_name": "数学", "class_name": "高一(3)班", "day_of_week": 0, "start_time": time(10, 10), "end_time": time(10, 55)},
    {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 0, "start_time": time(14, 0), "end_time": time(14, 45)},
    
    # 周二
    {"course_name": "数学", "class_name": "高一(2)班", "day_of_week": 1, "start_time": time(8, 0), "end_time": time(8, 45)},
    {"course_name": "数学", "class_name": "高一(3)班", "day_of_week": 1, "start_time": time(9, 0), "end_time": time(9, 45)},
    {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 1, "start_time": time(10, 10), "end_time": time(10, 55)},
    
    # 周三
    {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 2, "start_time": time(8, 0), "end_time": time(8, 45)},
    {"course_name": "数学", "class_name": "高一(2)班", "day_of_week": 2, "start_time": time(9, 0), "end_time": time(9, 45)},
    {"course_name": "数学", "class_name": "高一(3)班", "day_of_week": 2, "start_time": time(14, 0), "end_time": time(14, 45)},
    
    # 周四
    {"course_name": "数学", "class_name": "高一(3)班", "day_of_week": 3, "start_time": time(8, 0), "end_time": time(8, 45)},
    {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 3, "start_time": time(9, 0), "end_time": time(9, 45)},
    {"course_name": "数学", "class_name": "高一(2)班", "day_of_week": 3, "start_time": time(10, 10), "end_time": time(10, 55)},
    
    # 周五
    {"course_name": "数学", "class_name": "高一(2)班", "day_of_week": 4, "start_time": time(8, 0), "end_time": time(8, 45)},
    {"course_name": "数学", "class_name": "高一(3)班", "day_of_week": 4, "start_time": time(9, 0), "end_time": time(9, 45)},
    {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 4, "start_time": time(14, 0), "end_time": time(14, 45)},
    
    # 周六（可选）
    # {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 5, "start_time": time(8, 0), "end_time": time(8, 45)},
    
    # 周日（可选）
    # {"course_name": "数学", "class_name": "高一(1)班", "day_of_week": 6, "start_time": time(8, 0), "end_time": time(8, 45)},
]


async def import_mock_schedules():
    """导入Mock课表数据"""
    print("=" * 50)
    print("📅 开始导入Mock课表数据")
    print("=" * 50)
    
    # 初始化数据库
    await init_db()
    print("✅ 数据库初始化完成")
    
    async with AsyncSessionLocal() as db:
        # 查找用户（默认使用 teacher001）
        result = await db.execute(
            select(User).where(User.username == "teacher001")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ 未找到用户 'teacher001'，请先创建用户")
            print("\n💡 提示：可以通过以下方式创建用户：")
            print("   1. 访问 http://localhost:8000/api/docs")
            print("   2. 使用 POST /api/v1/auth/register 接口")
            print("   3. 或运行用户创建脚本")
            return
        
        print(f"✅ 找到用户: {user.username} (ID: {user.id})")
        
        # 检查是否已有课表
        result = await db.execute(
            select(Schedule).where(Schedule.user_id == user.id)
        )
        existing_schedules = result.scalars().all()
        
        if existing_schedules:
            print(f"⚠️  用户已有 {len(existing_schedules)} 条课表记录")
            response = input("是否清空现有课表并重新导入？(y/n): ")
            if response.lower() == 'y':
                for schedule in existing_schedules:
                    await db.delete(schedule)
                await db.commit()
                print("✅ 已清空现有课表")
            else:
                print("❌ 取消导入")
                return
        
        # 创建新课表
        created_count = 0
        for schedule_data in MOCK_SCHEDULES:
            schedule = Schedule(
                user_id=user.id,
                **schedule_data
            )
            db.add(schedule)
            created_count += 1
        
        await db.commit()
        
        print(f"✅ 成功创建 {created_count} 条课表记录")
        print("\n📋 导入的课表概览：")
        print("-" * 50)
        
        # 显示导入的课表
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for schedule_data in MOCK_SCHEDULES:
            day_name = day_names[schedule_data["day_of_week"]]
            time_str = f"{schedule_data['start_time'].strftime('%H:%M')}-{schedule_data['end_time'].strftime('%H:%M')}"
            print(f"  {day_name} {time_str} | {schedule_data['course_name']} | {schedule_data['class_name']}")
        
        print("=" * 50)
        print("🎉 Mock课表数据导入完成！")
        print("\n💡 提示：")
        print("   1. 现在可以启动后端服务查看课表")
        print("   2. 前端首页将显示智能课表日历")
        print("   3. 可以通过 API 或前端界面管理课表")


if __name__ == "__main__":
    try:
        asyncio.run(import_mock_schedules())
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
