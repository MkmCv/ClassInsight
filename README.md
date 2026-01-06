# ClassInsight AI - 课堂行为智能分析系统

## 环境配置

### 1. 激活 Conda 环境
```bash
conda activate Yolo-vHeat
```

### 2. 安装后端依赖

#### 2.1 安装基础依赖
```bash
cd "H:\毕业设计\System\backend"
pip install -r requirements.txt
```

#### 2.2 安装 Ultralytics (YOLO-vHeat)

**方法 1: 使用安装脚本（推荐）**

Windows:
```powershell
cd "H:\毕业设计\System\backend"
.\install_ultralytics.ps1
```

Linux/Mac:
```bash
cd "H:\毕业设计\System\backend"
chmod +x install_ultralytics.sh
./install_ultralytics.sh
```

**方法 2: 手动安装**

1. 首先安装 PyTorch（根据您的 CUDA 版本选择）：
```bash
# CUDA 12.1
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# CUDA 11.8
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118

# CPU 版本
pip install torch==2.1.0 torchvision==0.16.0
```

2. 进入 yolo-vheat 目录并安装 ultralytics（可编辑模式）：
```bash
cd "H:\毕业设计\System\Model components\yolo-vheat"
pip install -e .
```

3. 验证安装：
```bash
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('✅ 安装成功！')"
```

## 启动服务

### 1. 启动后端 API 服务
```bash
cd "H:\毕业设计\System\backend"
python run.py
```

后端服务将在 `http://localhost:8000` 启动
API 文档: `http://localhost:8000/api/docs`

### 2. 创建初始用户

#### 2.1 创建超级管理员账号（必需）

```bash
cd "H:\毕业设计\System\backend"
python create_super_admin.py
```

**默认账号信息**：
- 用户名: `superadmin`
- 密码: `superadmin123`
- 邮箱: `2013119322@qq.com`

⚠️ **重要**：首次登录后请立即修改密码！

#### 2.2 创建普通用户（可选）

访问 API 文档 `http://localhost:8000/api/docs`，使用 `POST /api/v1/auth/register` 创建用户：

```json
{
  "username": "teacher001",
  "email": "teacher@example.com",
  "password": "123456",
  "role": "teacher",
  "unit": "实验中学",
  "class_name": "高一(1)班"
}
```

**注意**：注册接口只能创建 `teacher` 或 `admin` 角色，不能创建 `super_admin` 角色。

### 3. 启动前端服务
```bash
cd "H:\毕业设计\System\System\frontend"
streamlit run app.py
```

前端服务将在 `http://localhost:8501` 启动

## 系统说明

### 系统架构

系统分为两个独立的 Streamlit 应用：

1. **普通系统** (`System/frontend/`)
   - 端口：8501（默认）
   - 用户：教师、管理员
   - 功能：视频上传、行为分析、教学建议、用户管理、课表管理

2. **超级管理员系统** (`System/super_admin/`)
   - 端口：8502
   - 用户：超级管理员
   - 功能：登录安全配置、模型管理

### 启动超级管理员系统

```bash
cd "H:\毕业设计\System\System\super_admin"
streamlit run app.py --server.port 8502
```

访问地址：`http://localhost:8502`

## 注意事项

1. **超级管理员账号**：首次使用需要运行 `create_super_admin.py` 创建账号
2. **密码安全**：默认密码为 `superadmin123`，请首次登录后立即修改
3. **端口冲突**：确保两个系统使用不同端口（8501 和 8502）
4. **数据库**：确保后端服务已启动，数据库已初始化