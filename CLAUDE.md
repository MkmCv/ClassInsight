# CLAUDE.md

本文件为 AI 助手（Claude / Cursor 等）提供在 **ClassInsight** 仓库中工作的指引。人类贡献者也可作为速查参考。

---

## 1. 项目是什么

ClassInsight 是一套**课堂教学行为智能分析系统**：教师上传课堂录像 → 自研 **YOLO-vHeat** 多模型检测师生行为 → 时间窗聚合统计 → 行为分析 / 教学优化建议 / AI 教学顾问，并带三级角色权限与登录安全。

- **算法侧**（创新点）：YOLO-vHeat，独立仓库 [YOLO12-vHeat](https://github.com/MkmCv/YOLO12-vHeat)，本仓库以 git 子模块 `model/yolo-vheat` 引入。
- **系统侧**：FastAPI 后端 + 两套 Streamlit 前端。

---

## 2. 仓库结构

```
.
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/endpoints/   # 路由：auth/videos/analysis/optimization/admin/agent/schedules/...
│   │   ├── core/               # config、database、security
│   │   ├── models/             # SQLAlchemy ORM 实体
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── services/           # video_processor / behavior_analyzer / login_service / email_service
│   │   ├── ml/                 # MultiModelDetector、BehaviorClassifier、weights/
│   │   └── agent/              # LangGraph + 通义千问 教学顾问
│   ├── scripts/          # 建账号、导课表、检测可视化等工具脚本
│   ├── storage/          # SQLite 库 + 上传视频（视频/权重不入库）
│   ├── main.py           # FastAPI 应用本体（应用入口在此，不是 app/main.py）
│   └── run.py            # 开发启动脚本
├── frontend/
│   ├── app/              # 教师/管理员端（:8501）
│   └── super_admin/      # 超级管理员端（:8502）
├── model/
│   └── yolo-vheat/       # git 子模块 → YOLO12-vHeat（提供定制版 ultralytics）
└── docs/                 # 项目文档（见 docs/README.md）
```

---

## 3. 环境与运行（重要）

- **OS**：Windows；**Shell**：优先用 **CMD**（PowerShell 与 conda 偶有兼容问题）。
- **Conda 环境名**：`backup`，所有 Python 操作前先 `conda activate backup`。
- **编码**：后端 `run.py` 含 emoji，CMD 默认 GBK 会 `UnicodeEncodeError`。运行前先 `chcp 65001` 并 `set PYTHONIOENCODING=utf-8`。

```cmd
:: 后端 -> http://localhost:8000 （API 文档 /api/docs）
conda activate backup
chcp 65001 & set PYTHONIOENCODING=utf-8
cd backend
python run.py

:: 教师/管理员前端 -> http://localhost:8501
conda activate backup
cd frontend\app
streamlit run app.py

:: 超级管理员前端 -> http://localhost:8502
conda activate backup
cd frontend\super_admin
streamlit run app.py --server.port 8502
```

常用脚本（在 `backend/` 下运行）：

```cmd
python scripts\create_super_admin.py     :: 创建超级管理员
python scripts\mock_schedules.py          :: 导入示例课表
python scripts\visualize_detection.py     :: 检测结果可视化
```

默认超管：`superadmin / superadmin123`（首次登录请改密）。

---

## 4. 算法侧关键事实（答辩 / 改动前必读）

- 本 fork 为 **ultralytics 8.3.63**，原生包含 YOLOv12 的 `A2C2f`（区域注意力 / R-ELAN）与 `C3k2`。
- 创新点：在 `ultralytics/nn/modules/block.py` 实现 **vHeat 热传导算子**（`HeatConductionOperator` / `HeatBottleneck` / `C2fHeat` / `SPPFHeat`），用 **DCT → 指数热扩散衰减 → IDCT** 获得全局感受野（约 O(N^1.5)）。
- **模型配置对照**（同骨架、仅全局建模模块不同，可直接消融）：
  - `ultralytics/cfg/models/v12/yolov12.yaml` —— 你的版本，A2C2f 全部替换为 `C2fHeat`。
  - `ultralytics/cfg/models/v12/yolov12-a2c2f.yaml` —— 官方 A2C2f 基线。
- **准确表述**：是「用 vHeat 的 C2fHeat **替换** YOLOv12 的 A2C2f」，不是「在 A2C2f 之上叠加」。模型保留 v12 宏观拓扑，但已不含区域注意力。

后端检测通过 `from ultralytics import YOLO` 调用，需先在子模块以可编辑模式安装：`cd model/yolo-vheat && pip install -e .`。

---

## 5. 后端数据流（视频 → 结果）

```
POST /api/v1/videos/upload
  → 存视频、建 Video(processing)、BackgroundTasks 调 process_video_task
  → OpenCV 按 VIDEO_PROCESS_FPS(默认1fps) 抽帧
  → MultiModelDetector.detect（4 个权重分工 + 跨模型 NMS）
  → BehaviorClassifier.classify_frame（英文检测框 → 中文师生语义）
  → 10 秒非重叠窗聚合
  → 写 AnalysisTimeline / AnalysisSummary / AnalysisAnomaly
  → Video(completed)
分析/优化/Agent 端点消费上述结果。
```

四个检测权重（放在 `backend/app/ml/weights/`，`.pt` 不入库）：
`comprehensive_scene_best.pt`、`student_learning_best.pt`、`student_discussion_best.pt`、`student_posture_best.pt`。

---

## 6. 已知占位 / 演示逻辑（改动或评估时注意）

- **无权重时回退 mock**：缺 `.pt` 时 `video_processor` 用 `generate_mock_detections()` 生成假数据；演示前务必放好权重。
- **权重路径不一致**：检测器实际读 `app/ml/weights/`，而 `init_directories()` 建的是 `backend/ml/weights/`。
- `optimization/recommendations` 是**规则阈值引擎**；`agent/chat` 才是 LLM；两者不同源。
- `optimization/highlights` 当前为**硬编码时间段**。
- 时间线只写 **10s 窗**，API 的 `window=60` 二次聚合、`anomalies` 的 Z-score `threshold` 均未实现。
- `requires_captcha` 仅提示前端，后端登录接口未强制校验验证码；refresh token 无刷新端点。
- `microteaching` 仅有文档 `docs/behavior/microteaching.md`，无代码实现。

---

## 7. 子模块工作流（model/yolo-vheat）

```bash
# 首次克隆主仓库
git clone --recurse-submodules <ClassInsight 仓库地址>
git submodule update --init --recursive   # 已普通克隆时补拉

# 修改算法：在子模块内提交并推送到 YOLO12-vHeat
cd model/yolo-vheat
git add . && git commit -m "..." && git push origin HEAD:main

# 回到主仓库记录新的子模块指针
cd ../..
git add model/yolo-vheat && git commit -m "chore: bump yolo-vheat 子模块"
```

> Windows 上若报 "dubious ownership"：
> `git config --global --add safe.directory 'H:/毕业设计/System/model/yolo-vheat'`

---

## 8. 约定

- **不要**提交：模型权重（`*.pt/*.pth`）、视频、数据集、`*.db-shm/*.db-wal`、临时会话（`temp_sessions/`、`last_login.json`）。
- 远端：GitHub [ClassInsight](https://github.com/MkmCv/ClassInsight)（`github`）与 GitLab（`origin`）双远端，推送时按需各推一次。
- 文件 / 工具操作优先用 CMD + conda，路径含中文时注意编码。
- 改完后端代码需重启服务；前端有约 60s 缓存。
- 更多文档见 `docs/README.md`、`backend/README.md`、`frontend/README.md`、`model/README.md`。
```
