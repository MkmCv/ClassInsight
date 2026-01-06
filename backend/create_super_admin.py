"""
创建超级管理员账号脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from sqlalchemy import select


async def create_super_admin():
    """创建超级管理员账号"""
    # 初始化数据库
    await init_db()
    
    # 默认超级管理员账号信息
    username = "superadmin"
    email = "2013119320@qq.com"
    password = "superadmin123"  # 默认密码，首次登录后请修改
    
    async with AsyncSessionLocal() as session:
        try:
            # 检查是否已存在
            result = await session.execute(
                select(User).where(User.username == username)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                if existing_user.role == UserRole.SUPER_ADMIN.value:
                    print(f"✅ 超级管理员账号已存在: {username}")
                    print(f"   角色: {existing_user.role}")
                    print(f"   邮箱: {existing_user.email}")
                    return
                else:
                    # 更新为超级管理员
                    existing_user.role = UserRole.SUPER_ADMIN.value
                    existing_user.password_hash = get_password_hash(password)
                    await session.commit()
                    print(f"✅ 已更新用户为超级管理员: {username}")
                    print(f"   新密码: {password}")
                    return
            
            # 创建新账号
            super_admin = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                role=UserRole.SUPER_ADMIN.value,
                unit="系统管理员",
                is_active=1
            )
            
            session.add(super_admin)
            await session.commit()
            
            print("=" * 50)
            print("✅ 超级管理员账号创建成功！")
            print("=" * 50)
            print(f"用户名: {username}")
            print(f"密码: {password}")
            print(f"邮箱: {email}")
            print(f"角色: {UserRole.SUPER_ADMIN.value}")
            print("=" * 50)
            print("⚠️  重要提示：")
            print("   1. 请首次登录后立即修改密码")
            print("   2. 请妥善保管账号信息")
            print("   3. 建议使用强密码")
            print("=" * 50)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建失败: {str(e)}")
            raise


if __name__ == "__main__":
    print("正在创建超级管理员账号...")
    asyncio.run(create_super_admin())

