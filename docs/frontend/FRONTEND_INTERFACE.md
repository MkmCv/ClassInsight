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
- **参数**:
  - `file`: 视频文件
  - `class_name`: 班级名称
  - `course_name`: 课程名称
  - `lesson_date`: 上课日期 (YYYY-MM-DD)
  - `teacher_name`: 授课教师 (新增)
- **响应**: `{ "task_id": "uuid", "status": "processing", "video_id": 1 }`

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

#### 2.4.1 删除视频 ✅ 已实现
- **接口**: `DELETE /videos/{video_id}`
- **权限**: Owner (只能删除自己上传的) 或 Admin
- **响应**: `204 No Content`（前端兼容 200/204）
- **前端位置**: `pages/2_📤_视频上传.py` 第 80-97 行
- **UI 交互**:
  - 每行视频右侧有 🗑️ 删除按钮
  - 点击后弹出确认对话框（防止误删）
  - 确认后删除并自动刷新列表

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

#### 2.11 AI 教学顾问对话 ✅ 已实现
- **接口**: `POST /agent/chat`
- **请求**:
```json
{
  "video_id": 1,
  "messages": [
    {"role": "user", "content": "这节课的整体表现如何？"},
    {"role": "assistant", "content": "..."}
  ]
}
```
- **响应**:
```json
{
  "content": "根据分析数据，这节课整体表现良好...",
  "video_id": 1
}
```
- **前端位置**: `pages/4_💡_教学建议.py` Tab 2

#### 2.11.1 AI 教学顾问对话（流式） ✅ 已实现
- **接口**: `POST /agent/chat/stream`
- **请求**: 同上
- **响应**: Server-Sent Events (SSE)
```
data: {"status": "start"}
data: {"content": "根据"}
data: {"content": "分析"}
...
data: {"status": "done"}
```

#### 2.11.2 获取分析上下文（调试用）
- **接口**: `GET /agent/context/{video_id}`
- **响应**: Agent 将使用的格式化分析数据

---

### 🤖 AI 教学顾问前端实现说明

**文件位置**: `pages/4_💡_教学建议.py`

#### 页面设计特点
- **统一设计风格**：与系统其他页面保持一致的设计语言
- **卡片式布局**：使用圆角卡片、阴影效果，提升视觉层次
- **渐变配色**：AI 顾问区域使用紫色渐变背景，突出重要性
- **响应式布局**：适配不同屏幕尺寸

#### 视频选择
- 在**侧边栏**选择要分析的课堂视频
- 每个视频有**独立的聊天历史**（切换视频不会丢失之前的对话）
- 当前分析的视频信息显示在 AI 顾问 Tab 顶部的渐变卡片中

#### UI 组件
| 组件 | 说明 | 设计特点 |
|------|------|----------|
| 视频选择下拉框 | 侧边栏，显示日期+课程名+班级 | 统一侧边栏样式 |
| AI 顾问介绍卡片 | Tab 顶部渐变卡片 | 紫色渐变背景，白色文字 |
| 改进建议卡片 | 左侧建议列表 | 左侧彩色边框，优先级标签，阴影效果 |
| 精彩片段卡片 | 左侧片段展示 | 时间标签卡片，理由说明区域 |
| 雷达图 | 右侧能力模型 | 透明背景，双色对比 |
| 历史趋势图 | 右侧趋势线 | 主色调线条，网格背景 |
| 聊天消息列表 | 显示对话历史 | Streamlit 原生聊天组件 |
| 输入框 | 底部固定，支持回车发送 | 与清空按钮并排布局 |
| 清空对话按钮 | 重置当前视频的聊天历史 | 紧凑按钮样式 |

#### 状态管理
```python
# 每个视频独立的聊天历史
chat_key = f"chat_messages_{selected_video_id}"
st.session_state[chat_key] = [...]
```

#### 错误处理
- 连接超时：显示友好提示
- 后端未启动：提示用户启动后端
- API 错误：显示具体错误信息

#### 设计规范
- **颜色方案**：主色 `#4F46E5` (Indigo 600)，背景 `#F9FAFB`
- **圆角**：统一使用 `12px` 圆角
- **阴影**：卡片使用轻微阴影 `0 1px 3px rgba(0,0,0,0.1)`
- **间距**：统一使用 `20px` 和 `16px` 间距

---

### 👤 用户管理 (User Management)
**前端文件**: `pages/5_👤_用户管理.py`

#### 2.12 获取用户列表
- **接口**: `GET /users`
- **权限**: Admin
- **响应**: `[{"id": 1, "username": "...", "role": "teacher", ...}, ...]`

#### 2.13 创建新用户
- **接口**: `POST /auth/register`
- **权限**: Admin
- **请求**:
```json
{
  "username": "teacher002",
  "password": "secretpassword",
  "email": "teacher2@school.edu",
  "role": "teacher", // admin 或 teacher
  "unit": "Math Department",
  "class_name": "Grade 10 Class 2"
}
```
- **响应**: `201 Created`

#### 2.14 删除用户
- **接口**: `DELETE /users/{user_id}`
- **权限**: Admin
- **响应**: `200 OK`

---

## 3. 后端对接注意事项
1. **Mock 数据**: 开发阶段可直接使用 `mock_data.py` 中的数据结构。
2. **LLM 接入**: 后端需集成 OpenAI/LangChain 接口，并实现流式响应（StreamingResponse）。
3. **跨域问题**: 确保 FastAPI 配置了 CORS 允许前端端口访问。
4. **权限控制**: 确保所有 `/users/*` 接口验证当前用户 `role` 是否为 `admin`。
