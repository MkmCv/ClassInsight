"""
启动脚本 - 自动设置路径
"""
import os
import sys

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

print(f"工作目录: {os.getcwd()}")
print("正在启动 ClassInsight 后端服务...")

# 启动服务器
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )





