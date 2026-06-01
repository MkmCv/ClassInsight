# ClassInsight AI - 课堂行为智能分析系统

## 环境配置

### ⚠️ 重要提示：必须使用 CMD + conda 环境

所有 Python 相关操作都必须在 **CMD 终端** 中，并先激活 **backup** conda 环境：

```cmd
conda activate backup
```

**为什么必须这样做？**
- PowerShell 可能与 conda 环境有兼容性问题
- 确保 Python 路径和依赖正确加载
- 避免模块导入错误

### 1. 激活 Conda 环境（必需）

打开 **CMD 终端**（不是 PowerShell），然后执行：

```cmd
conda activate backup
```

### 2. 安装后端依赖

#### 2.1 安装基础依赖

在 **CMD 终端** 中执行：

```cmd
conda activate backup
cd H:\毕业设计\System\backend
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

在 **CMD 终端** 中执行：

```cmd
conda activate backup

```

后端服务将在 `http://localhost:8000` 启动
API 文档: `http://localhost:8000/api/docs`

### 2. 创建初始用户

#### 2.1 创建超级管理员账号（必需）

在 **CMD 终端** 中执行：

```cmd
conda activate backup
cd H:\毕业设计\System\backend
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

### 3. 导入课表数据（可选）

有两种方式可以导入课表数据：

#### 方法1：通过前端界面导入（推荐）

1. 登录管理员账号
2. 进入「📅 课表管理」页面
3. 点击「📥 批量导入」标签页
4. 选择「使用预设Mock数据」或「手动输入JSON数据」
5. 选择教师并点击「开始导入」

**优点**：可视化界面，操作简单，支持实时预览

#### 方法2：通过命令行脚本导入

在 **CMD 终端** 中执行：

```cmd
conda activate backup
cd H:\毕业设计\System\backend
python mock_schedules.py
```

**说明**：
- 脚本会自动查找用户 `teacher001`（如果不存在会提示先创建用户）
- 会创建一周的课表数据（周一到周五，每天3-4节课）
- 如果用户已有课表，会询问是否清空后重新导入
- 导入后，前端首页的"智能课表日历"将显示这些课程

**自定义课表数据**：
- 前端方式：在「批量导入」页面修改JSON数据
- 脚本方式：编辑 `backend/mock_schedules.py` 文件中的 `MOCK_SCHEDULES` 列表

### 4. 启动前端服务

在 **CMD 终端** 中执行：

```cmd
conda activate backup
cd H:\毕业设计\System\System\frontend
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

在 **CMD 终端** 中执行：

```cmd
conda activate backup
cd H:\毕业设计\System\System\super_admin
streamlit run app.py --server.port 8502
```

访问地址：`http://localhost:8502`

## 常见问题

### ❓ 为什么教师看不到课表？

如果导入课表后，教师用户在首页看不到课表，请按以下步骤排查：

**1. 验证课表是否成功导入**

访问 API 文档查询：
1. 打开 `http://localhost:8000/api/docs`
2. 找到 `GET /api/v1/schedules/my` 接口
3. 使用教师账号的 Token 进行测试
4. 查看返回的课表数据

**2. 检查用户 ID 是否匹配**

导入脚本默认为 `teacher001` 导入课表，确保：
- 该用户已存在
- 用户 ID 与导入的课表中的 `user_id` 一致

**3. 检查后端服务状态**

确认后端服务正常运行在 `http://localhost:8000`

**4. 清除前端缓存**

前端课表数据有 60 秒缓存，可以：
- 等待 60 秒后刷新页面
- 清除浏览器缓存
- 重启前端服务

**5. 通过管理员界面查看**

使用管理员账号登录，在「📅 课表管理」页面查看是否有课表数据。

### ❓ 运行脚本时提示模块找不到？

**原因**：未在正确的 conda 环境中运行

**解决方法**：
1. 打开 **CMD** 终端（不是 PowerShell）
2. 执行 `conda activate backup`
3. 确认环境激活成功后再运行脚本

### ❓ 数据库文件在哪里？

数据库文件位置：`backend/storage/classinsight.db`

可以使用 SQLite 工具查看数据库内容。

## 注意事项

1. **⚠️ 必须使用 CMD + conda 环境**：所有 Python 脚本都必须在 CMD 中激活 `backup` 环境后运行
2. **超级管理员账号**：首次使用需要运行 `create_super_admin.py` 创建账号
3. **密码安全**：默认密码为 `superadmin123`，请首次登录后立即修改
4. **端口冲突**：确保两个系统使用不同端口（8501 和 8502）
5. **数据库**：确保后端服务已启动，数据库已初始化
6. **课表数据**：导入课表时确保 `user_id` 与实际教师 ID 匹配