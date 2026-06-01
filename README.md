# ClassInsight AI — 课堂行为智能分析系统

基于 **YOLO-vHeat** 算法的课堂教学行为智能分析平台。系统通过对课堂视频进行目标检测与行为识别，自动统计师生行为、生成时间序列与雷达图，并结合大模型给出教学优化建议，面向中小学教师与教研管理者。

---

## ✨ 主要功能

- **视频上传与处理**：上传课堂视频，后台异步进行帧采样、行为检测与结果入库。
- **行为分析**：整课行为统计、时间序列趋势、异常片段检测、师生行为相关性分析。
- **教学建议**：基于分析结果生成雷达图、改进建议与优秀教学片段，集成 AI 教学顾问。
- **课表管理**：教师课表的录入、批量导入与日历展示。
- **用户与权限**：教师 / 管理员 / 超级管理员三级角色，含登录安全策略与失败审计。
- **超级管理员系统**：独立前端，负责登录安全配置与模型管理。

---

## 🧱 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Streamlit（多页应用） |
| 后端 | FastAPI + Uvicorn（异步） |
| 数据库 | SQLite + SQLAlchemy（异步 ORM） |
| 认证 | JWT（python-jose）+ bcrypt |
| 计算机视觉 | YOLO-vHeat（基于 ultralytics 二次开发）+ OpenCV |
| AI 顾问 | 通义千问（DashScope）+ LangGraph |

---

## 📂 项目结构

```
System/                       # 仓库根目录
├── backend/                  # 后端 FastAPI 服务
│   ├── app/                  # 应用代码（api / models / services / ml / agent / core）
│   ├── scripts/              # 工具脚本（建账号、导课表、检测可视化）
│   ├── storage/              # 数据库与视频存储（视频/权重不入库）
│   ├── main.py               # FastAPI 应用入口
│   ├── run.py                # 启动脚本
│   └── requirements.txt
├── frontend/                 # 前端 Streamlit 应用
│   ├── app/                  # 教师 / 管理员端（默认端口 8501）
│   └── super_admin/          # 超级管理员端（默认端口 8502）
├── model/                    # 模型组件
│   ├── yolo-vheat/           # YOLO-vHeat（ultralytics 二次开发，可编辑安装）
│   ├── vHeat-main/           # vHeat 主干网络
│   └── dataset/              # 数据集（不入库）
├── docs/                     # 项目文档（见 docs/README.md）
└── api_spec.yaml             # OpenAPI 规格
```

---

## 🚀 快速开始

> ⚠️ **环境要求**：Windows 下请使用 **CMD 终端**并先激活 conda 环境 `backup`，以保证 Python 路径与依赖正确加载（避免 PowerShell 的兼容性问题）。

### 1. 激活环境

```cmd
conda activate backup
```

### 2. 安装后端依赖

```cmd
cd H:\毕业设计\System\backend
pip install -r requirements.txt
```

### 3. 安装 YOLO-vHeat（ultralytics 可编辑模式）

```cmd
:: 先按 CUDA 版本安装 PyTorch（示例为 CUDA 12.1）
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

:: 以可编辑模式安装 ultralytics（含 vHeat 模块）
cd H:\毕业设计\System\model\yolo-vheat
pip install -e .

:: 验证
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('OK')"
```

> 模型权重放在 `backend/app/ml/weights/`（`.pt` 文件不纳入 git）。

### 4. 启动后端服务

```cmd
cd H:\毕业设计\System\backend
python run.py
```

- API 地址：`http://localhost:8000`
- API 文档：`http://localhost:8000/api/docs`

### 5. 创建账号

```cmd
cd H:\毕业设计\System\backend
python scripts\create_super_admin.py
```

默认超级管理员：用户名 `superadmin` / 密码 `superadmin123`（**首次登录请立即修改密码**）。

普通教师 / 管理员可通过 API 文档的 `POST /api/v1/auth/register` 创建（注册接口不能创建 `super_admin`）。

### 6. 启动前端

教师 / 管理员端：

```cmd
cd H:\毕业设计\System\frontend\app
streamlit run app.py
```
访问 `http://localhost:8501`

超级管理员端：

```cmd
cd H:\毕业设计\System\frontend\super_admin
streamlit run app.py --server.port 8502
```
访问 `http://localhost:8502`

### 7. （可选）导入示例课表

```cmd
cd H:\毕业设计\System\backend
python scripts\mock_schedules.py
```
或在前端「📅 课表管理 → 批量导入」中以可视化方式导入。

---

## 📖 文档

完整文档见 [`docs/`](./docs/README.md)，主要包含：

- [后端 API 接口](./docs/backend/api.md) ・ [数据库设计](./docs/backend/database-design.md)
- [前端架构](./docs/frontend/architecture.md) ・ [用户使用指南](./docs/frontend/user-guide.md)
- [行为分析算法](./docs/behavior/) ・ [超级管理员系统](./docs/super-admin.md)
- [论文与答辩材料](./docs/thesis/)

---

## ❓ 常见问题

- **运行脚本提示找不到模块**：未激活 `backup` 环境，或未使用 CMD。请先 `conda activate backup`。
- **`from ultralytics import` 报错**：重命名 `model/` 目录后需重新执行 `pip install -e .`（可编辑安装记录的是旧路径）。
- **教师看不到课表**：确认后端已启动、课表 `user_id` 与教师 ID 匹配，前端有 60 秒缓存，可稍候或刷新。
- **数据库位置**：`backend/storage/classinsight.db`，可用 SQLite 工具查看。
- **端口冲突**：教师端 8501、超管端 8502，确保不冲突。
