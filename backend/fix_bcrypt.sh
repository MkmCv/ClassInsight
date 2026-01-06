#!/bin/bash
# 修复 bcrypt 兼容性问题 - Bash 脚本

echo "========================================"
echo "修复 bcrypt 兼容性问题"
echo "========================================"
echo ""

# 检查是否在 conda 环境中
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "当前 Conda 环境: $CONDA_DEFAULT_ENV"
else
    echo "警告: 未检测到 Conda 环境，请先激活您的环境"
    echo "例如: conda activate Backup"
    echo ""
fi

echo "步骤 1: 卸载旧版本..."
pip uninstall bcrypt passlib -y

echo ""
echo "步骤 2: 安装兼容版本..."
pip install bcrypt==4.0.1
pip install "passlib[bcrypt]>=1.7.4"

echo ""
echo "步骤 3: 验证安装..."
python -c "import bcrypt; print(f'✅ bcrypt 版本: {bcrypt.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ bcrypt 导入失败"
else
    echo "✅ bcrypt 安装成功"
fi

python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print('✅ passlib 安装成功')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ passlib 导入失败"
else
    echo "✅ passlib 安装成功"
fi

echo ""
echo "========================================"
echo "修复完成！请重启后端服务"
echo "========================================"

