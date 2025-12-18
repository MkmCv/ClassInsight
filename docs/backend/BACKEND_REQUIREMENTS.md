# ⚙️ 后端需求规格说明书 (Backend Requirements Specification)

本文档详细定义了“ClassInsight 课堂行为分析系统”的后端开发需求，涵盖API接口、数据库设计、业务逻辑及非功能性要求。

## 1. 系统架构概览

- **核心框架**: FastAPI (Python)
- **数据库**: PostgreSQL (推荐) 或 SQLite (开发环境)
- **ORM**: SQLAlchemy / Tortoise-ORM
- **异步任务**: Celery + Redis (用于视频处理)
- **AI 模型集成**: vHeat 算法库 (需封装为服务)
- **LLM 集成**: OpenAI API 兼容接口 (用于教学建议)

---

## 2. API 接口详解

### 🔐 认证模块 (Auth)

#### `POST /api/v1/auth/login`
- **功能**: 用户登录，返回 JWT Token。
- **请求**: `{ "username": "...", "password": "..." }`
- **响应**:
  ```json
  {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "user": { "id": 1, "username": "teacher001", "role": "teacher", "unit": "..." }
  }
  ```

### 🏠 首页模块 (Dashboard)

#### `GET /api/v1/dashboard/schedule`
- **功能**: 获取今日课程表。
- **逻辑**: 根据当前用户 ID 查询 `schedule` 表，返回今日课程。
- **响应**:
  ```json
  {
    "schedule": [
      {
        "time": "08:00 - 08:45",
        "subject": "数学",
        "class": "高一(1)班",
        "status": "finished" // finished, ongoing, upcoming
      }
    ]
  }
  ```

#### `GET /api/v1/dashboard/metrics`
- **功能**: 获取首页核心指标卡片数据。
- **逻辑**: 聚合最近一周的课堂分析数据，计算平均值和环比变化。
- **响应**:
  ```json
  {
    "interaction_rate": {"value": "35%", "delta": "+5%"}, // 互动率 = 讨论时长 / 总时长
    "focus_rate": {"value": "88%", "delta": "+2%"},      // 专注度 = 1 - 低头率
    "pending_videos": 2
  }
  ```

### 📤 视频管理模块 (Video)

#### `POST /api/v1/videos/upload`
- **功能**: 上传视频文件并创建处理任务。
- **流程**:
  1. 接收文件，存储到对象存储或本地文件系统。
  2. 在数据库创建 `video` 记录，状态为 `pending`。
  3. 触发 Celery 异步任务进行 AI 分析。
  4. 返回 `task_id` 和 `video_id`。

#### `GET /api/v1/videos/{task_id}/status`
- **功能**: 轮询视频处理状态。
- **响应**: `{ "status": "processing", "progress": 0.45, "step": "正在检测行为..." }`

#### `GET /api/v1/videos/list`
- **功能**: 获取视频列表（用于下拉框）。
- **响应**: `[{ "video_id": 1, "lesson_date": "2025-10-23", "course_name": "数学", "class_name": "高一(1)班" }]`

### 📈 分析模块 (Analysis)

#### `GET /api/v1/analysis/{video_id}/summary`
- **功能**: 获取整课行为统计汇总。
- **数据源**: `analysis_summary` 表。
- **响应结构**:
  ```json
  {
    "video_id": 1,
    "duration": 2700,
    "behavior_summary": {
      "discuss": {"count": 45, "total_duration": 800, "percentage": 29.6},
      "hand-raising": {"count": 12, "total_duration": 180, "percentage": 6.7},
      "read": {...}, "write": {...}, "BowHead": {...}, "TurnHead": {...}
    },
    "teacher_behavior": {
      "teacher": {...}, "guide": {...}
    }
  }
  ```

#### `GET /api/v1/analysis/{video_id}/timeline`
- **功能**: 获取时间序列数据（用于折线图和堆叠图）。
- **参数**: `window` (默认 60s)。
- **响应**:
  ```json
  {
    "timeline": [
      {
        "timestamp": 0,
        "behaviors": { "discuss": 5, "read": 15, "BowHead": 2 } // 这里的数值是该时间窗口内的平均人数或发生次数
      },
      ...
    ]
  }
  ```

#### `GET /api/v1/analysis/{video_id}/anomalies`
- **功能**: 获取异常事件。
- **逻辑**: 基于阈值（如低头率 > 30%）自动筛选异常片段。
- **响应**:
  ```json
  {
    "anomalies": [
      {
        "start_time": 1200, "end_time": 1380,
        "type": "high_bowhead_rate",
        "severity": "medium",
        "description": "低头率持续偏高（>30%）"
      }
    ]
  }
  ```

### 💡 优化与建议模块 (Optimization)

#### `GET /api/v1/optimization/{video_id}/radar`
- **功能**: 计算教学能力雷达图得分。
- **算法**:
  - 互动率: 归一化(讨论时长 + 举手次数)
  - 专注度: 1 - 低头率
  - 活跃度: 举手频率
  - 教师引导: 教师 `guide` 行为占比
  - 多媒体使用: `screen` 使用时长占比

#### `GET /api/v1/optimization/{video_id}/recommendations`
- **功能**: 生成改进建议和精彩片段。
- **响应**: 包含 `recommendations` (建议列表) 和 `highlights` (高分片段)。

#### `POST /api/v1/ai/chat`
- **功能**: AI 教学顾问对话。
- **技术**: 调用 LLM (如 GPT-4, Claude, 或本地模型)，传入当前课程的分析数据作为 Context。
- **响应**: SSE (Server-Sent Events) 流式输出。

---

## 3. 数据库设计建议 (ER Draft)

- **users**: `id, username, password_hash, role, unit`
- **videos**: `id, user_id, filepath, status, duration, meta_info`
- **analysis_timeline**: `id, video_id, timestamp, behavior_counts(JSON)` - 存储每秒或每10秒的原始数据
- **analysis_summary**: `id, video_id, summary_json` - 存储聚合后的整课数据，加速查询
- **analysis_anomalies**: `id, video_id, start_time, end_time, type, description`
- **schedules**: `id, user_id, course_name, class_name, start_time, end_time`

---

## 4. 核心业务逻辑说明

1.  **视频处理流水线**:
    - 上传 -> 解码 -> 抽帧 (如 1fps) -> vHeat 模型推理 -> 原始检测结果 -> 轨迹平滑 -> 统计聚合 -> 存入数据库。
2.  **异常检测算法**:
    - 使用滑动窗口（如 5分钟）计算特定行为（如低头）的占比，如果超过阈值（如 30%）且持续一定时间，则标记为异常。
3.  **数据安全**:
    - 视频文件需鉴权访问。
    - 敏感数据（如学生人脸）建议在推理后不存储原始图片，仅存储脱敏后的统计数据。

---

## 5. 开发阶段 Mock 策略

后端开发初期，可以先提供 Mock 接口（直接返回上述 JSON 结构），以便前端进行联调。待 vHeat 算法集成完毕后，再替换为真实数据。

