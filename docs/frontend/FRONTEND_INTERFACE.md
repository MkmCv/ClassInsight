# 📡 前端对接接口文档 (Frontend Interface Specification)

本文档定义了前端页面所需的数据结构和 API 接口。后端开发需遵循此规范提供数据。

## 1. 基础配置
- **API Base URL**: `/api/v1`
- **认证方式**: Bearer Token (JWT)

---

## 2. 页面接口需求

### 🏠 首页 (Dashboard)
**前端文件**: `pages/1_🏠_首页.py`

#### 2.1 获取今日课程表
- **接口**: `GET /dashboard/schedule`
- **响应**:
```json
{
  "schedule": [
    {
      "time": "08:00 - 08:45",
      "subject": "数学 (代数)",
      "class": "高一(1)班",
      "status": "finished" // finished, ongoing, upcoming
    },
    {
      "time": "10:00 - 10:45",
      "subject": "数学 (几何)",
      "class": "高一(3)班",
      "status": "upcoming",
      "tags": ["Next", "15分钟后"]
    }
  ]
}
```

#### 2.2 获取核心指标
- **接口**: `GET /dashboard/metrics`
- **响应**:
```json
{
  "interaction_rate": {"value": "35%", "delta": "+5%"},
  "focus_rate": {"value": "88%", "delta": "+2%"},
  "teaching_pace": "适中",
  "pending_videos": 2
}
```

---

### 📤 视频上传 (Upload)
**前端文件**: `pages/2_📤_视频上传.py`

#### 2.3 上传视频
- **接口**: `POST /videos/upload`
- **参数**: `file`, `class_name`, `course_name`, `lesson_date`
- **响应**: `{ "task_id": "uuid", "status": "processing" }`

#### 2.4 查询处理进度 (轮询)
- **接口**: `GET /videos/{task_id}/status`
- **响应**:
```json
{
  "status": "processing", // processing, completed, failed
  "progress": 0.45,       // 0-1
  "step": "正在进行目标检测..." // 当前步骤描述
}
```

---

### 📈 行为分析 (Analysis)
**前端文件**: `pages/3_📈_行为分析.py`

#### 2.5 获取视频列表（筛选下拉框）
- **接口**: `GET /videos/list`
- **响应**: `[{"id": 1, "label": "2023-10-23 数学 (高一1班)"}, ...]`

#### 2.6 获取整课汇总数据
- **接口**: `GET /analysis/{video_id}/summary`
- **响应**: (参考 `mock_data.py` 中的 `get_mock_summary` 结构)

#### 2.7 获取时间序列数据 (折线图)
- **接口**: `GET /analysis/{video_id}/timeline`
- **响应**: (参考 `mock_data.py` 中的 `get_mock_timeline` 结构)

#### 2.8 获取异常事件
- **接口**: `GET /analysis/{video_id}/anomalies`
- **响应**: (参考 `mock_data.py` 中的 `get_mock_anomalies` 结构)

---

### 💡 教学建议 (Optimization & LLM)
**前端文件**: `pages/4_💡_教学建议.py`

#### 2.9 获取教学能力雷达图数据
- **接口**: `GET /optimization/{video_id}/radar`
- **响应**:
```json
{
  "categories": ["互动率", "专注度", "活跃度", "教师引导", "多媒体使用"],
  "current_scores": [4.2, 3.5, 2.8, 4.5, 3.2],
  "history_avg_scores": [3.8, 3.9, 3.2, 3.5, 2.9]
}
```

#### 2.10 获取改进建议
- **接口**: `GET /optimization/{video_id}/recommendations`
- **响应**: (参考 `mock_data.py` 中的 `get_mock_recommendations` 结构)

#### 2.11 AI 教学顾问对话 (流式)
- **接口**: `POST /ai/chat` (Server-Sent Events 或 WebSocket)
- **请求**: `{ "video_id": 1, "messages": [{"role": "user", "content": "..."}] }`
- **响应**: 流式输出文本

---

## 3. 后端对接注意事项
1. **Mock 数据**: 开发阶段可直接使用 `mock_data.py` 中的数据结构。
2. **LLM 接入**: 后端需集成 OpenAI/LangChain 接口，并实现流式响应（StreamingResponse）。
3. **跨域问题**: 确保 FastAPI 配置了 CORS 允许前端端口访问。

