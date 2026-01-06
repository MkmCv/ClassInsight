#!/bin/bash
# Ultralytics (YOLO-vHeat) 安装脚本 (Linux/Mac)
# 用于从 yolo-vheat 目录安装 ultralytics

echo "========================================"
echo "  Ultralytics (YOLO-vHeat) 安装脚本"
echo "========================================"
echo ""

# 检查是否在正确的目录
CURRENT_DIR=$(pwd)
echo "当前目录: $CURRENT_DIR"

# 检查 yolo-vheat 目录是否存在
# 注意：请根据您的实际路径修改
YOLO_VHEAT_PATH="../Model components/yolo-vheat"
if [ ! -d "$YOLO_VHEAT_PATH" ]; then
    echo "❌ 错误: 找不到 yolo-vheat 目录: $YOLO_VHEAT_PATH"
    echo "请确认路径是否正确，或修改脚本中的路径。"
    exit 1
fi

echo "✅ 找到 yolo-vheat 目录: $YOLO_VHEAT_PATH"
echo ""

# 步骤 1: 检查 PyTorch 是否已安装
echo "步骤 1: 检查 PyTorch 安装..."
if python -c "import torch; print('✅ PyTorch 已安装:', torch.__version__)" 2>/dev/null; then
    echo ""
else
    echo "⚠️  PyTorch 未安装或无法导入"
    echo "请先安装 PyTorch："
    echo "  pip install torch==2.1.0 torchvision==0.16.0"
    echo "或根据您的 CUDA 版本选择："
    echo "  # CUDA 12.1"
    echo "  pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121"
    echo "  # CUDA 11.8"
    echo "  pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118"
    read -p "是否继续安装 ultralytics？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi
echo ""

# 步骤 2: 进入 yolo-vheat 目录并安装
echo "步骤 2: 安装 ultralytics (可编辑模式)..."
cd "$YOLO_VHEAT_PATH" || exit 1
echo "已切换到: $(pwd)"

# 检查 pyproject.toml 是否存在
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 找不到 pyproject.toml 文件"
    exit 1
fi

# 安装 ultralytics（可编辑模式）
echo "正在安装 ultralytics..."
pip install -e .

if [ $? -eq 0 ]; then
    echo "✅ ultralytics 安装成功！"
else
    echo "❌ ultralytics 安装失败"
    exit 1
fi
echo ""

# 步骤 3: 验证安装
echo "步骤 3: 验证安装..."
if python -c "from ultralytics import YOLO; print('✅ ultralytics 导入成功')" 2>/dev/null; then
    echo ""
else
    echo "⚠️  验证失败"
fi

# 检查 vHeat 模块
echo "检查 vHeat 模块..."
if python -c "from ultralytics.nn.modules import C2fHeat; print('✅ C2fHeat 模块可用')" 2>/dev/null; then
    echo ""
else
    echo "⚠️  C2fHeat 模块不可用"
    echo "这可能意味着 vHeat 模块未正确集成"
fi

echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"

# 返回原目录
cd "$CURRENT_DIR" || exit 1



