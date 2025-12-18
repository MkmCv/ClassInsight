# 📡 API接口文档

> 基于OpenAPI 3.0规范，用于课堂行为分析系统

## 📋 目录

1. [认证模块](#1-认证模块)
2. [视频管理模块](#2-视频管理模块)
3. [行为分析模块](#3-行为分析模块)
4. [教学优化模块](#4-教学优化模块)
5. [报告导出模块](#5-报告导出模块)

---

## 1. 认证模块

### 1.1 用户注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "teacher001",        # 必填，3-50字符
  "password": "SecurePass123!",    # 必填，至少8位
  "email": "teacher@example.com",  # 必填，邮箱格式
  "role": "teacher",               # 必填，teacher | admin
  "unit": "岭南师范学院",          # 可选，单位
  "class_name": "高一(1)班"        # 可选，班级
}
```

**响应示例：**
```json
{
  "user_id": 1,
  "username": "teacher001",
  "message": "注册成功"
}
```

**状态码：**
- `201` - 注册成功
- `400` - 参数错误
- `409` - 用户名已存在

---

### 1.2 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "teacher001",
  "password": "SecurePass123!"
}
```

**响应示例：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "teacher001",
    "role": "teacher"
  }
}
```

**状态码：**
- `200` - 登录成功
- `401` - 用户名或密码错误

---

### 1.3 获取当前用户信息
```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "id": 1,
  "username": "teacher001",
  "email": "teacher@example.com",
  "role": "teacher",
  "unit": "岭南师范学院",
  "class_name": "高一(1)班",
  "created_at": "2025-10-23T10:00:00Z"
}
```

---

### 1.4 修改密码
```http
PUT /api/v1/auth/password
Authorization: Bearer {token}
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

**响应示例：**
```json
{
  "message": "密码修改成功"
}
```

---

## 2. 视频管理模块

### 2.1 上传视频
```http
POST /api/v1/videos/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <video_file>              # 视频文件（MP4/AVI/MOV，最大2GB）
class_name: "高一(1)班"          # 可选
course_name: "数学"              # 可选
lesson_date: "2025-10-23"        # 可选，YYYY-MM-DD格式
```

**响应示例：**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_id": 1,
  "status": "processing",
  "message": "视频已上传，正在处理中"
}
```

**状态码：**
- `202` - 已接受，正在处理
- `400` - 文件格式不支持或参数错误

**说明：**
- 视频处理是异步的，需要轮询状态接口获取处理进度
- 支持格式：MP4, AVI, MOV
- 最大文件大小：2GB

---

### 2.2 获取视频列表
```http
GET /api/v1/videos?page=1&page_size=20&class_name=xxx&status=completed
Authorization: Bearer {token}
```

**查询参数：**
- `page` - 页码（默认1）
- `page_size` - 每页数量（默认20，最大100）
- `class_name` - 班级名称筛选（可选）
- `course_name` - 课程名称筛选（可选）
- `status` - 状态筛选（可选）：uploaded, processing, completed, failed

**响应示例：**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "video_id": 1,
      "filename": "class_20251023.mp4",
      "class_name": "高一(1)班",
      "course_name": "数学",
      "lesson_date": "2025-10-23",
      "duration": 3600,
      "status": "completed",
      "created_at": "2025-10-23T10:00:00Z"
    }
  ]
}
```

---

### 2.3 获取视频详情
```http
GET /api/v1/videos/{video_id}
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "video_id": 1,
  "filename": "class_20251023.mp4",
  "class_name": "高一(1)班",
  "course_name": "数学",
  "lesson_date": "2025-10-23",
  "duration": 3600,
  "file_size": 1073741824,
  "fps": 30.0,
  "resolution": "1920x1080",
  "total_frames": 108000,
  "status": "completed",
  "user_id": 1,
  "created_at": "2025-10-23T10:00:00Z"
}
```

---

### 2.4 查询处理状态
```http
GET /api/v1/videos/{video_id}/status
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "video_id": 1,
  "status": "processing",
  "progress": 0.65,              # 0-1
  "current_frame": 1950,
  "total_frames": 3000,
  "estimated_time_remaining": 120  # 秒
}
```

**状态说明：**
- `uploaded` - 已上传，等待处理
- `processing` - 正在处理
- `completed` - 处理完成
- `failed` - 处理失败（error_message字段包含错误信息）

---

### 2.5 删除视频
```http
DELETE /api/v1/videos/{video_id}
Authorization: Bearer {token}
```

**状态码：**
- `204` - 删除成功
- `404` - 视频不存在

**说明：**
- 删除视频会同时删除所有相关数据（检测结果、分析报告等）

---

## 3. 行为分析模块

### 3.1 获取行为统计（整课聚合）
```http
GET /api/v1/analysis/{video_id}/summary
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "video_id": 1,
  "duration": 3600,
  "total_frames": 3000,
  "behavior_summary": {
    "discuss": {
      "count": 45,           # 发生次数
      "total_duration": 1200, # 总时长（秒）
      "percentage": 33.3     # 占比（%）
    },
    "hand-raising": {
      "count": 12,
      "total_duration": 180,
      "percentage": 5.0
    },
    "read": { ... },
    "write": { ... },
    "BowHead": { ... },
    "TurnHead": { ... }
  },
  "teacher_behavior": {
    "teacher": { "count": 1, "duration": 3600, "percentage": 100.0 },
    "blackboard-writing": { "count": 8, "duration": 600, "percentage": 16.7 },
    "screen": { "count": 5, "duration": 1200, "percentage": 33.3 }
  }
}
```

**说明：**
- 返回整节课的行为统计汇总
- 包括学生行为（6类）和教师行为（5类）
- 每个行为包含：发生次数、总时长、占比

---

### 3.2 获取时间序列数据（用于可视化）
```http
GET /api/v1/analysis/{video_id}/timeline?window=10
Authorization: Bearer {token}
```

**查询参数：**
- `window` - 时间窗口大小（秒），可选值：10, 60（默认10）

**响应示例：**
```json
{
  "video_id": 1,
  "window_size": 10,
  "timeline": [
    {
      "timestamp": 0,      # 起始时间（秒）
      "behaviors": {
        "discuss": 3,      # 该窗口内检测到的数量
        "hand-raising": 1,
        "read": 15,
        "write": 8,
        "BowHead": 2,
        "TurnHead": 1
      }
    },
    {
      "timestamp": 10,
      "behaviors": { ... }
    }
    // ... 更多时间点
  ]
}
```

**说明：**
- 用于绘制时间序列图表（堆叠面积图、折线图等）
- 数据按时间窗口聚合，减少数据量
- 10秒窗口适合详细分析，60秒窗口适合整体趋势

---

### 3.3 获取异常时段
```http
GET /api/v1/analysis/{video_id}/anomalies?threshold=2.0
Authorization: Bearer {token}
```

**查询参数：**
- `threshold` - 异常检测阈值（Z-score倍数，默认2.0）

**响应示例：**
```json
{
  "video_id": 1,
  "anomalies": [
    {
      "start_time": 1200,  # 秒
      "end_time": 1500,
      "type": "high_bowhead_rate",
      "severity": "medium",
      "description": "低头率超过阈值（>30%）",
      "behavior_stats": {
        "BowHead": {
          "count": 20,
          "total_duration": 300,
          "percentage": 35.0
        }
      }
    }
  ]
}
```

**异常类型：**
- `high_bowhead_rate` - 低头率过高
- `low_interaction_rate` - 互动率过低
- `high_turnhead_rate` - 转头率过高
- `low_attention_rate` - 注意力率过低

**严重程度：**
- `low` - 轻微异常
- `medium` - 中等异常
- `high` - 严重异常

---

### 3.4 行为成因分析
```http
GET /api/v1/analysis/{video_id}/causation
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "video_id": 1,
  "correlations": [
    {
      "student_behavior": "discuss",
      "teacher_behavior": "guide",
      "correlation_coefficient": 0.75,  # Pearson相关系数
      "lag_time": 5,  # 滞后时间（秒）
      "interpretation": "教师引导行为与学生讨论行为呈正相关，滞后5秒"
    }
  ],
  "overlap_analysis": [
    {
      "student_behavior": "read",
      "context": "screen",
      "overlap_rate": 0.65,
      "description": "65%的阅读行为发生在屏幕使用期间"
    }
  ]
}
```

**说明：**
- `correlations` - 相关性分析，计算学生行为与教师行为的Pearson相关系数
- `overlap_analysis` - 重叠分析，计算学生行为与场景元素的时间重叠率

---

## 4. 教学优化模块

### 4.1 获取优化建议
```http
GET /api/v1/optimization/{video_id}/recommendations
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "video_id": 1,
  "recommendations": [
    {
      "type": "interaction",
      "priority": "high",
      "title": "增加互动频次",
      "description": "讨论占比不足（当前15%，建议≥30%），建议增加分组讨论环节",
      "suggested_actions": [
        "在课程中段（20-30分钟）增加小组讨论",
        "设置讨论问题，引导学生互动"
      ]
    },
    {
      "type": "attention",
      "priority": "medium",
      "title": "关注学生注意力",
      "description": "低头率在15-20分钟时段较高（35%），建议调整教学节奏",
      "suggested_actions": [
        "增加提问频次",
        "使用多媒体吸引注意力"
      ]
    }
  ]
}
```

**建议类型：**
- `interaction` - 互动改进
- `attention` - 注意力提升
- `rhythm` - 节奏调整
- `engagement` - 参与度提升

**优先级：**
- `low` - 低优先级
- `medium` - 中优先级
- `high` - 高优先级

---

### 4.2 跨课次对比
```http
GET /api/v1/optimization/compare?video_ids=1,2,3&metrics=all
Authorization: Bearer {token}
```

**查询参数：**
- `video_ids` - 视频ID列表，逗号分隔（必填）
- `metrics` - 对比指标（可选）：all, interaction, attention, engagement（默认all）

**响应示例：**
```json
{
  "comparison": [
    {
      "video_id": 1,
      "lesson_date": "2025-10-20",
      "metrics": {
        "interaction_rate": 0.25,
        "attention_rate": 0.85,
        "engagement_score": 0.75
      }
    },
    {
      "video_id": 2,
      "lesson_date": "2025-10-23",
      "metrics": {
        "interaction_rate": 0.30,
        "attention_rate": 0.88,
        "engagement_score": 0.80
      }
    }
  ],
  "trends": {
    "interaction_rate": "increasing",
    "attention_rate": "stable",
    "engagement_score": "increasing"
  }
}
```

**趋势说明：**
- `increasing` - 上升趋势
- `decreasing` - 下降趋势
- `stable` - 稳定

---

### 4.3 获取优秀课堂片段
```http
GET /api/v1/optimization/{video_id}/highlights?min_score=0.8
Authorization: Bearer {token}
```

**查询参数：**
- `min_score` - 最低质量评分（0-1，默认0.8）

**响应示例：**
```json
{
  "video_id": 1,
  "highlights": [
    {
      "start_time": 600,
      "end_time": 900,
      "score": 0.92,
      "reasons": [
        "互动占比高（35%）",
        "异常行为少（低头率<10%）",
        "教师引导与学生响应良好"
      ],
      "thumbnail_url": "/api/v1/videos/1/frames/600"
    }
  ]
}
```

**说明：**
- 根据预设指标阈值自动筛选高质量课堂片段
- 评分基于：互动占比、异常行为率、师生互动质量等

---

## 5. 报告导出模块

### 5.1 生成分析报告
```http
POST /api/v1/reports/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "video_id": 1,
  "include_charts": true,
  "include_recommendations": true,
  "report_type": "summary"  # summary | detailed | comparison
}
```

**响应示例：**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating",
  "estimated_time": 30  # 秒
}
```

**说明：**
- 报告生成是异步的，需要轮询状态接口
- 报告类型：
  - `summary` - 摘要报告（默认）
  - `detailed` - 详细报告
  - `comparison` - 对比报告（需要多个video_id）

---

### 5.2 查询报告状态
```http
GET /api/v1/reports/{report_id}
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "download_url": "/api/v1/reports/550e8400-e29b-41d4-a716-446655440000/download"
}
```

**状态：**
- `generating` - 生成中
- `completed` - 已完成
- `failed` - 生成失败（error_message字段包含错误信息）

---

### 5.3 下载报告
```http
GET /api/v1/reports/{report_id}/download
Authorization: Bearer {token}
```

**响应：**
- `200` - PDF文件（Content-Type: application/pdf）
- `404` - 报告不存在或未完成

---

## 🔐 认证说明

所有需要认证的接口都需要在请求头中添加JWT token：

```http
Authorization: Bearer {access_token}
```

token通过登录接口获取，有效期建议设置为24小时。

---

## 📝 数据模型说明

### 行为类别（全局ID映射）

**学生行为：**
- `BowHead` (ID: 1) - 低头
- `TurnHead` (ID: 2) - 转头
- `hand-raising` (ID: 3) - 举手
- `read` (ID: 4) - 阅读
- `write` (ID: 5) - 书写
- `discuss` (ID: 6) - 讨论

**教师行为：**
- `guide` (ID: 7) - 引导
- `answer` (ID: 8) - 回答
- `On-stage interaction` (ID: 9) - 上台互动
- `teacher` (ID: 10) - 教师
- `blackboard-writing` (ID: 11) - 板书
- `stand` (ID: 12) - 站立
- `screen` (ID: 13) - 屏幕
- `blackBoard` (ID: 14) - 黑板

---

## ⚠️ 注意事项

1. **异步处理**：视频上传和报告生成是异步的，需要轮询状态接口
2. **分页查询**：列表接口支持分页，建议每页不超过100条
3. **错误处理**：所有接口都可能返回错误，需要处理4xx和5xx状态码
4. **数据隐私**：系统不进行学生身份绑定，仅输出班级层面统计
5. **文件大小**：视频文件最大2GB，建议压缩后上传

---

## 🔄 典型使用流程

### 1. 用户登录
```http
POST /api/v1/auth/login
→ 获取 access_token
```

### 2. 上传视频
```http
POST /api/v1/videos/upload
→ 返回 video_id 和 task_id
```

### 3. 轮询处理状态
```http
GET /api/v1/videos/{video_id}/status
→ 等待 status = "completed"
```

### 4. 获取行为分析
```http
GET /api/v1/analysis/{video_id}/summary
GET /api/v1/analysis/{video_id}/timeline?window=10
GET /api/v1/analysis/{video_id}/anomalies
```

### 5. 获取优化建议
```http
GET /api/v1/optimization/{video_id}/recommendations
```

### 6. 生成报告
```http
POST /api/v1/reports/generate
→ 轮询报告状态
→ 下载PDF报告
```

---

**文档版本：** v1.0.0  
**最后更新：** 2025-10-23




