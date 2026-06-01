# Git 仓库重新初始化脚本
# 执行前请确保在 H:\毕业设计\System 目录下

Write-Host "开始重新初始化 Git 仓库..." -ForegroundColor Green

# 1. 删除现有的 .git 目录（如果存在）
if (Test-Path ".git") {
    Write-Host "删除现有的 .git 目录..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force .git
    Write-Host "已删除 .git 目录" -ForegroundColor Green
} else {
    Write-Host ".git 目录不存在，跳过删除步骤" -ForegroundColor Yellow
}

# 2. 初始化新的 git 仓库
Write-Host "初始化新的 Git 仓库..." -ForegroundColor Yellow
git init
Write-Host "Git 仓库初始化完成" -ForegroundColor Green

# 3. 配置安全目录
Write-Host "配置 Git 安全目录..." -ForegroundColor Yellow
$currentDir = (Get-Location).Path
git config --global --add safe.directory $currentDir
Write-Host "安全目录配置完成" -ForegroundColor Green

# 4. 添加远程仓库
Write-Host "添加远程仓库..." -ForegroundColor Yellow
git remote add origin git@gitlab.com:MkmCv/classvision-vheat.git
Write-Host "远程仓库添加完成" -ForegroundColor Green

# 5. 创建并切换到 main 分支
Write-Host "创建 main 分支..." -ForegroundColor Yellow
git checkout -b main
Write-Host "已切换到 main 分支" -ForegroundColor Green

# 6. 添加所有文件
Write-Host "添加所有文件到暂存区..." -ForegroundColor Yellow
git add .
Write-Host "文件添加完成" -ForegroundColor Green

# 7. 提交
Write-Host "提交更改..." -ForegroundColor Yellow
git commit -m "Initial commit: 项目初始化"
Write-Host "提交完成" -ForegroundColor Green

# 8. 推送到远程
Write-Host "推送到远程仓库..." -ForegroundColor Yellow
git push -u origin main --force
Write-Host "推送完成！" -ForegroundColor Green

Write-Host "`n仓库重新初始化完成！" -ForegroundColor Cyan















