# Ultralytics (YOLO-vHeat) 安装脚本
# 用于从 yolo-vheat 目录安装 ultralytics

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ultralytics (YOLO-vHeat) 安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
$currentDir = Get-Location
Write-Host "当前目录: $currentDir" -ForegroundColor Yellow

# 检查 yolo-vheat 目录是否存在
$yoloVheatPath = "H:\毕业设计\System\Model components\yolo-vheat"
if (-not (Test-Path $yoloVheatPath)) {
    Write-Host "❌ 错误: 找不到 yolo-vheat 目录: $yoloVheatPath" -ForegroundColor Red
    Write-Host "请确认路径是否正确，或修改脚本中的路径。" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 找到 yolo-vheat 目录: $yoloVheatPath" -ForegroundColor Green
Write-Host ""

# 步骤 1: 检查 PyTorch 是否已安装
Write-Host "步骤 1: 检查 PyTorch 安装..." -ForegroundColor Cyan
try {
    $torchVersion = python -c "import torch; print(torch.__version__)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PyTorch 已安装: $torchVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠️  PyTorch 未安装或无法导入" -ForegroundColor Yellow
        Write-Host "请先安装 PyTorch：" -ForegroundColor Yellow
        Write-Host "  pip install torch==2.1.0 torchvision==0.16.0" -ForegroundColor White
        Write-Host "或根据您的 CUDA 版本选择：" -ForegroundColor Yellow
        Write-Host "  # CUDA 12.1" -ForegroundColor White
        Write-Host "  pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121" -ForegroundColor White
        Write-Host "  # CUDA 11.8" -ForegroundColor White
        Write-Host "  pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor White
        $continue = Read-Host "是否继续安装 ultralytics？(y/n)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            exit 0
        }
    }
} catch {
    Write-Host "⚠️  无法检查 PyTorch，继续安装 ultralytics..." -ForegroundColor Yellow
}
Write-Host ""

# 步骤 2: 进入 yolo-vheat 目录并安装
Write-Host "步骤 2: 安装 ultralytics (可编辑模式)..." -ForegroundColor Cyan
Set-Location $yoloVheatPath
Write-Host "已切换到: $(Get-Location)" -ForegroundColor Yellow

# 检查 pyproject.toml 是否存在
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ 错误: 找不到 pyproject.toml 文件" -ForegroundColor Red
    exit 1
}

# 安装 ultralytics（可编辑模式）
Write-Host "正在安装 ultralytics..." -ForegroundColor Yellow
pip install -e .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ ultralytics 安装成功！" -ForegroundColor Green
} else {
    Write-Host "❌ ultralytics 安装失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 步骤 3: 验证安装
Write-Host "步骤 3: 验证安装..." -ForegroundColor Cyan
try {
    $result = python -c "from ultralytics import YOLO; print('✅ ultralytics 导入成功')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result -ForegroundColor Green
    } else {
        Write-Host "⚠️  验证失败: $result" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  验证时出现错误" -ForegroundColor Yellow
}

# 检查 vHeat 模块
Write-Host ""
Write-Host "检查 vHeat 模块..." -ForegroundColor Cyan
try {
    $vheatCheck = python -c "from ultralytics.nn.modules import C2fHeat; print('✅ C2fHeat 模块可用')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $vheatCheck -ForegroundColor Green
    } else {
        Write-Host "⚠️  C2fHeat 模块不可用: $vheatCheck" -ForegroundColor Yellow
        Write-Host "这可能意味着 vHeat 模块未正确集成" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  检查 vHeat 模块时出现错误" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# 返回原目录
Set-Location $currentDir



