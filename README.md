<div align="center">

# 🎓 ClassInsight AI

**基于 YOLO-vHeat 的课堂教学行为智能分析系统**

通过对课堂视频进行目标检测与行为识别，自动统计师生课堂行为、生成可视化分析，并结合大模型给出教学优化建议。

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)
![YOLO-vHeat](https://img.shields.io/badge/CV-YOLO--vHeat-00BFFF)

</div>

---

## 📖 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [系统架构](#️-系统架构)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [文档](#-文档)
- [常见问题](#-常见问题)
- [说明](#-说明)

---

## 📌 项目简介

ClassInsight 面向中小学教师与教研管理者，提供从 **课堂视频上传 → 行为检测 → 数据分析 → 教学建议** 的完整闭环：

- 后端基于 **FastAPI** 提供异步 REST API，使用 **YOLO-vHeat** 多模型协同完成课堂行为检测；
- 前端基于 **Streamlit** 构建教师/管理员端与超级管理员端两套界面；
- 集成 **大模型教学顾问**，将分析结果转化为可执行的教学优化建议。

> 视觉算法（YOLO-vHeat，基于 ultralytics 二次开发并集成 vHeat 模块）已拆分为**独立项目**单独维护。

---

## ✨ 功能特性

| 模块 | 说明 |
|------|------|
| 📤 视频管理 | 上传课堂视频，后台异步帧采样、行为检测与结果入库 |
| 📈 行为分析 | 整课行为统计、时间序列趋势、异常片段检测、师生行为相关性分析 |
| 💡 教学建议 | 雷达图、跨课次对比、改进建议、优秀片段，集成 AI 教学顾问 |
| 📅 课表管理 | 教师课表录入、批量导入与日历展示 |
| 👤 用户与权限 | 教师 / 管理员 / 超级管理员三级角色，登录安全策略与失败审计 |
| 👑 超级管理员 | 独立前端，负责登录安全配置与模型管理 |

---

## 🏗️ 系统架构

```
┌────────────────────┐      ┌────────────────────┐
│  Streamlit 前端     │      │  Streamlit 超管端   │
│  教师 / 管理员 :8501 │      │  超级管理员   :8502  │
└─────────┬──────────┘      └─────────┬──────────┘
          │            HTTP / JWT     │
          └──────────────┬────────────┘
                         ▼
              ┌────────────────────┐
              │   FastAPI 后端 :8000 │
              │  api / services / ml │
              └─────────┬──────────┘
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                 ▼
  ┌──────────┐   ┌─────────────┐   ┌──────────────┐
  │ SQLite   │   │ YOLO-vHeat  │   │  大模型顾问   │
  │ (ORM)    │   │  行为检测    │   │ DashScope    │
  └──────────┘   └─────────────┘   └──────────────┘
```

---

## 🧱 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Streamlit（多页应用） |
| 后端 | FastAPI + Uvicorn（异步） |
| 数据库 | SQLite + SQLAlchemy（异步 ORM） |
| 认证 | JWT（python-jose）+ bcrypt |
| 计算机视觉 | YOLO-vHeat（ultralytics 二次开发）+ OpenCV |
| AI 顾问 | 通义千问（DashScope）+ LangGraph |

---

## 📂 项目结构

```
.
├── backend/                  # 后端 FastAPI 服务
│   ├── app/                  # 应用代码（api / models / services / ml / agent / core）
│   ├── scripts/              # 工具脚本（建账号、导课表、检测可视化）
│   ├── storage/              # 数据库与视频存储（视频/权重不入库）
│   ├── main.py               # FastAPI 应用入口
│   ├── run.py                # 启动脚本
│   └── requirements.txt
├── frontend/                 # 前端 Streamlit 应用
│   ├── app/                  # 教师 / 管理员端（:8501）
│   └── super_admin/          # 超级管理员端（:8502）
├── model/                    # 视觉算法（YOLO-vHeat，供后端 ultralytics 可编辑安装）
├── docs/                     # 项目文档（见 docs/README.md）
└── api_spec.yaml             # OpenAPI 规格
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+（推荐使用 Conda 管理环境）
- 支持 CUDA 的 GPU（行为检测推荐，CPU 亦可运行）
- Windows 用户建议在 **CMD** 中先激活 Conda 环境后再运行 Python 命令

```bash
conda create -n classinsight python=3.10
conda activate classinsight
```

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 安装视觉算法（YOLO-vHeat，可编辑模式）

```bash
# 按 CUDA 版本安装 PyTorch（示例 CUDA 12.1）
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# 安装定制版 ultralytics（含 vHeat 模块）
cd model/yolo-vheat
pip install -e .

# 验证
python -c "from ultralytics import YOLO; from ultralytics.nn.modules import C2fHeat; print('OK')"
```

> 模型权重放在 `backend/app/ml/weights/`（`.pt` 文件不纳入版本控制）。

### 3. 启动后端

```bash
cd backend
python run.py
```

- API 地址：<http://localhost:8000>
- API 文档：<http://localhost:8000/api/docs>

### 4. 初始化账号

```bash
cd backend
python scripts/create_super_admin.py
```

默认超级管理员：`superadmin` / `superadmin123` —— **首次登录请立即修改密码**。
普通教师 / 管理员可通过 API 文档的 `POST /api/v1/auth/register` 创建。

### 5. 启动前端

```bash
# 教师 / 管理员端 -> http://localhost:8501
cd frontend/app
streamlit run app.py

# 超级管理员端 -> http://localhost:8502
cd frontend/super_admin
streamlit run app.py --server.port 8502
```

### 6.（可选）导入示例课表

```bash
cd backend
python scripts/mock_schedules.py
```

或在前端「📅 课表管理 → 批量导入」中可视化导入。

---

## 📖 文档

完整文档见 [`docs/`](./docs/README.md)：

- 🔌 [后端 API 接口](./docs/backend/api.md) ・ 🗄️ [数据库设计](./docs/backend/database-design.md)
- 🎨 [前端架构](./docs/frontend/architecture.md) ・ 📘 [用户使用指南](./docs/frontend/user-guide.md)
- 🧠 [行为分析算法](./docs/behavior/) ・ 👑 [超级管理员系统](./docs/super-admin.md)

---

## ❓ 常见问题

<details>
<summary>运行脚本提示找不到模块？</summary>

未激活 Conda 环境或未使用 CMD。请先 `conda activate <你的环境>` 再运行。
</details>

<details>
<summary><code>from ultralytics import ...</code> 报错？</summary>

`model/` 目录位置变化后，可编辑安装记录的旧路径会失效，需在 `model/yolo-vheat` 重新执行 `pip install -e .`。
</details>

<details>
<summary>教师看不到课表？</summary>

确认后端已启动、课表 `user_id` 与教师 ID 匹配；前端有 60 秒缓存，可稍候或刷新。
</details>

<details>
<summary>数据库在哪里？</summary>

`backend/storage/classinsight.db`，可用 SQLite 工具查看。运行时产生的 `*.db-shm/*.db-wal` 为临时文件，不纳入版本控制。
</details>

---

## 📎 说明

- 视觉算法（YOLO-vHeat）作为独立项目单独维护，本仓库聚焦系统侧（前后端）。
- 端口约定：后端 `8000`、教师端 `8501`、超管端 `8502`，请避免冲突。
