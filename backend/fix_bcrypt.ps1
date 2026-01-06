# 修复 bcrypt 兼容性问题 - PowerShell 脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复 bcrypt 兼容性问题" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在 conda 环境中
$condaEnv = $env:CONDA_DEFAULT_ENV
if ($condaEnv) {
    Write-Host "当前 Conda 环境: $condaEnv" -ForegroundColor Green
} else {
    Write-Host "警告: 未检测到 Conda 环境，请先激活您的环境" -ForegroundColor Yellow
    Write-Host "例如: conda activate Backup" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "步骤 1: 卸载旧版本..." -ForegroundColor Yellow
pip uninstall bcrypt passlib -y

Write-Host ""
Write-Host "步骤 2: 安装兼容版本..." -ForegroundColor Yellow
pip install bcrypt==4.0.1
pip install "passlib[bcrypt]>=1.7.4"

Write-Host ""
Write-Host "步骤 3: 验证安装..." -ForegroundColor Yellow
python -c "import bcrypt; print(f'✅ bcrypt 版本: {bcrypt.__version__}')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ bcrypt 导入失败" -ForegroundColor Red
} else {
    Write-Host "✅ bcrypt 安装成功" -ForegroundColor Green
}

python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print('✅ passlib 安装成功')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ passlib 导入失败" -ForegroundColor Red
} else {
    Write-Host "✅ passlib 安装成功" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "修复完成！请重启后端服务" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

