# 数据库设计文档

## 1. 概述

ClassInsight 系统使用 **SQLite**（开发环境）/ **PostgreSQL**（生产环境）作为数据库，采用 **SQLAlchemy 2.0 异步 ORM** 进行数据访问。

### 技术栈
- **ORM**: SQLAlchemy 2.0 (Async)
- **数据库驱动**: aiosqlite (SQLite) / asyncpg (PostgreSQL)
- **迁移工具**: Alembic (可选)

### 数据库配置
```python
# 开发环境
DATABASE_URL = "sqlite+aiosqlite:///./storage/classinsight.db"

# 生产环境
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/classinsight"
```

---

## 2. ER 图

```
┌─────────────────────┐                    ┌─────────────────────────┐
│       users         │                    │         videos          │
├─────────────────────┤                    ├─────────────────────────┤
│ id          PK      │───┐                │ id              PK      │
│ username    UNIQUE  │   │                │ user_id         FK ─────┼──┐
│ email       UNIQUE  │   │                │ filename                │  │
│ password_hash       │   │                │ filepath                │  │
│ role                │   │                │ file_size               │  │
│ unit                │   │                │ duration                │  │
│ class_name          │   │                │ fps                     │  │
│ created_at          │   │                │ resolution              │  │
│ updated_at          │   │                │ total_frames            │  │
└─────────────────────┘   │                │ class_name              │  │
         │                │                │ course_name             │  │
         │                │                │ lesson_date             │  │
         │                │                │ status                  │  │
         │                │                │ progress                │  │
         │                │                │ current_frame           │  │
         │                │                │ error_message           │  │
         │                │                │ created_at              │  │
         │                │                │ updated_at              │  │
         │                │                │ processed_at            │  │
         │                │                └─────────────────────────┘  │
         │                │                           │                 │
         │                │          ┌────────────────┼─────────────────┤
         │                │          │                │                 │
         │                │          ▼                ▼                 │
         │                │  ┌───────────────┐ ┌───────────────┐       │
         │                │  │analysis_      │ │analysis_      │       │
         │                │  │timeline       │ │summary        │       │
         │                │  ├───────────────┤ ├───────────────┤       │
         │                │  │ id        PK  │ │ id        PK  │       │
         │                │  │ video_id  FK ─┼─│ video_id  FK ─┼───────┤
         │                │  │ timestamp     │ │ summary_json  │       │
         │                │  │ window_size   │ │ total_detect  │       │
         │                │  │ behavior_     │ │ interaction_  │       │
         │                │  │   counts(JSON)│ │   rate        │       │
         │                │  │ detections    │ │ attention_    │       │
         │                │  │   (JSON)      │ │   rate        │       │
         │                │  │ created_at    │ │ engagement_   │       │
         │                │  │               │ │   score       │       │
         │                │  └───────────────┘ │ created_at    │       │
         │                │                    │ updated_at    │       │
         │                │                    └───────────────┘       │
         │                │                           │                 │
         │                │                           ▼                 │
         │                │                    ┌───────────────┐       │
         │                │                    │analysis_      │       │
         │                │                    │anomalies      │       │
         │                │                    ├───────────────┤       │
         │                │                    │ id        PK  │       │
         │                │                    │ video_id  FK ─┼───────┘
         │                │                    │ start_time    │
         │                │                    │ end_time      │
         │                │                    │ anomaly_type  │
         │                │                    │ severity      │
         │                │                    │ description   │
         │                │                    │ behavior_stats│
         │                │                    │   (JSON)      │
         │                │                    │ created_at    │
         │                │                    └───────────────┘
         │                │
         │                │    ┌─────────────────────┐
         │                └───▶│      schedules      │
         │                     ├─────────────────────┤
         │                     │ id          PK      │
         └────────────────────▶│ user_id     FK      │
                               │ course_name         │
                               │ class_name          │
                               │ day_of_week         │
                               │ start_time          │
                               │ end_time            │
                               │ created_at          │
                               │ updated_at          │
                               └─────────────────────┘
```

---

## 3. 表结构详细设计

### 3.1 用户表 (users)

存储系统用户信息，支持教师和管理员角色。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 用户ID |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 用户名 |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | 邮箱 |
| `password_hash` | VARCHAR(255) | NOT NULL | 密码哈希 (bcrypt) |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'teacher' | 角色: teacher/admin |
| `unit` | VARCHAR(100) | NULLABLE | 单位/学校 |
| `class_name` | VARCHAR(50) | NULLABLE | 班级 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| `updated_at` | DATETIME | ON UPDATE NOW | 更新时间 |

**索引**: `username`, `email`

**关联关系**:
- `1:N` → videos (一个用户可上传多个视频)
- `1:N` → schedules (一个用户有多条课程表记录)

---

### 3.2 视频表 (videos)

存储上传的课堂录像信息及处理状态。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 视频ID |
| `user_id` | INTEGER | FK(users.id), NOT NULL, INDEX | 所属用户 |
| `filename` | VARCHAR(255) | NOT NULL | 原始文件名 |
| `filepath` | VARCHAR(500) | NOT NULL | 存储路径 |
| `file_size` | INTEGER | NULLABLE | 文件大小(字节) |
| `duration` | FLOAT | NULLABLE | 视频时长(秒) |
| `fps` | FLOAT | NULLABLE | 帧率 |
| `resolution` | VARCHAR(20) | NULLABLE | 分辨率 (如 "1920x1080") |
| `total_frames` | INTEGER | NULLABLE | 总帧数 |
| `class_name` | VARCHAR(50) | NULLABLE | 班级 |
| `course_name` | VARCHAR(50) | NULLABLE | 课程名称 |
| `lesson_date` | DATE | NULLABLE | 上课日期 |
| `status` | VARCHAR(20) | NOT NULL, INDEX, DEFAULT 'uploaded' | 状态 |
| `progress` | FLOAT | DEFAULT 0.0 | 处理进度 (0-1) |
| `current_frame` | INTEGER | DEFAULT 0 | 当前处理帧 |
| `error_message` | TEXT | NULLABLE | 错误信息 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| `updated_at` | DATETIME | ON UPDATE NOW | 更新时间 |
| `processed_at` | DATETIME | NULLABLE | 处理完成时间 |

**status 枚举值**:
- `uploaded` - 已上传，等待处理
- `processing` - 正在处理
- `completed` - 处理完成
- `failed` - 处理失败

**索引**: `user_id`, `status`

**关联关系**:
- `N:1` → users (多个视频属于一个用户)
- `1:N` → analysis_timeline (一个视频有多条时间线记录)
- `1:1` → analysis_summary (一个视频对应一条汇总)
- `1:N` → analysis_anomalies (一个视频可能有多个异常)

---

### 3.3 时间序列分析表 (analysis_timeline)

存储每个时间窗口（默认10秒）的行为统计数据。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 记录ID |
| `video_id` | INTEGER | FK(videos.id), NOT NULL, INDEX | 所属视频 |
| `timestamp` | INTEGER | NOT NULL | 时间戳(秒) |
| `window_size` | INTEGER | DEFAULT 10 | 窗口大小(秒) |
| `behavior_counts` | JSON | NOT NULL | 行为计数 |
| `detections` | JSON | NULLABLE | 检测框数据 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |

**behavior_counts 结构示例**:
```json
{
  "teacher": 1,
  "guide": 0,
  "stand": 1,
  "screen": 1,
  "blackBoard": 0,
  "discuss": 3,
  "read": 8,
  "write": 5,
  "hand-raising": 1,
  "BowHead": 2,
  "TurnHead": 0
}
```

**detections 结构示例**:
```json
[
  {"category": "teacher", "bbox": [100, 50, 300, 400], "score": 0.95},
  {"category": "read", "bbox": [400, 200, 500, 350], "score": 0.87}
]
```

---

### 3.4 分析汇总表 (analysis_summary)

存储整课的聚合统计数据和核心指标。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 记录ID |
| `video_id` | INTEGER | FK(videos.id), UNIQUE, NOT NULL | 所属视频 |
| `summary_json` | JSON | NOT NULL | 汇总数据 |
| `total_detections` | INTEGER | DEFAULT 0 | 总检测数 |
| `interaction_rate` | FLOAT | NULLABLE | 互动率 (0-1) |
| `attention_rate` | FLOAT | NULLABLE | 专注度 (0-1) |
| `engagement_score` | FLOAT | NULLABLE | 参与度评分 (0-1) |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| `updated_at` | DATETIME | ON UPDATE NOW | 更新时间 |

**summary_json 结构示例**:
```json
{
  "behavior_summary": {
    "discuss": {
      "count": 156,
      "total_duration": 420,
      "percentage": 14.0
    },
    "read": {
      "count": 892,
      "total_duration": 1800,
      "percentage": 60.0
    },
    "teacher": {
      "count": 180,
      "total_duration": 2700,
      "percentage": 90.0
    }
  }
}
```

**指标计算公式**:
- `interaction_rate` = 讨论时长 / 视频总时长
- `attention_rate` = 1 - (低头时长 / 视频总时长)
- `engagement_score` = (interaction_rate + 举手次数/50) / 2

---

### 3.5 异常事件表 (analysis_anomalies)

存储检测到的课堂异常时段。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 记录ID |
| `video_id` | INTEGER | FK(videos.id), NOT NULL, INDEX | 所属视频 |
| `start_time` | INTEGER | NOT NULL | 开始时间(秒) |
| `end_time` | INTEGER | NOT NULL | 结束时间(秒) |
| `anomaly_type` | VARCHAR(50) | NOT NULL | 异常类型 |
| `severity` | VARCHAR(20) | NOT NULL | 严重程度 |
| `description` | TEXT | NOT NULL | 异常描述 |
| `behavior_stats` | JSON | NULLABLE | 相关行为统计 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |

**anomaly_type 常见值**:
- `high_bowhead_rate` - 低头率持续偏高
- `low_interaction` - 互动不足
- `attention_drop` - 注意力下降

**severity 枚举值**:
- `low` - 轻微
- `medium` - 中等
- `high` - 严重

---

### 3.6 课程表 (schedules)

存储教师的课程安排信息。

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 记录ID |
| `user_id` | INTEGER | FK(users.id), NOT NULL, INDEX | 所属用户 |
| `course_name` | VARCHAR(50) | NOT NULL | 课程名称 |
| `class_name` | VARCHAR(50) | NOT NULL | 班级 |
| `day_of_week` | INTEGER | NOT NULL | 星期几 (0=周一, 6=周日) |
| `start_time` | TIME | NOT NULL | 开始时间 |
| `end_time` | TIME | NOT NULL | 结束时间 |
| `created_at` | DATETIME | NOT NULL, DEFAULT NOW | 创建时间 |
| `updated_at` | DATETIME | ON UPDATE NOW | 更新时间 |

---

## 4. 关联关系总结

| 关系类型 | 主表 | 从表 | 外键 | 级联删除 |
|----------|------|------|------|----------|
| 1:N | users | videos | user_id | ✅ CASCADE |
| 1:N | users | schedules | user_id | ✅ CASCADE |
| 1:N | videos | analysis_timeline | video_id | ✅ CASCADE |
| 1:1 | videos | analysis_summary | video_id | ✅ CASCADE |
| 1:N | videos | analysis_anomalies | video_id | ✅ CASCADE |

---

## 5. 索引策略

| 表名 | 索引字段 | 索引类型 | 用途 |
|------|----------|----------|------|
| users | username | UNIQUE | 登录查询 |
| users | email | UNIQUE | 邮箱验证 |
| videos | user_id | B-TREE | 用户视频列表 |
| videos | status | B-TREE | 状态筛选 |
| analysis_timeline | video_id | B-TREE | 时间线查询 |
| analysis_timeline | (video_id, timestamp) | COMPOSITE | 时间范围查询 |
| analysis_summary | video_id | UNIQUE | 汇总查询 |
| analysis_anomalies | video_id | B-TREE | 异常列表 |
| schedules | user_id | B-TREE | 用户课表 |
| schedules | (user_id, day_of_week) | COMPOSITE | 今日课程 |

---

## 6. 数据量估算

假设一个教师每周上传 5 节课，每节课 45 分钟：

| 表名 | 每课记录数 | 每周记录数 | 每学期(20周) |
|------|-----------|-----------|--------------|
| videos | 1 | 5 | 100 |
| analysis_timeline | 270 (45min ÷ 10s) | 1,350 | 27,000 |
| analysis_summary | 1 | 5 | 100 |
| analysis_anomalies | ~3 | ~15 | ~300 |

**总数据量**: 每学期约 **27,500** 条记录（单用户）

---

## 7. 数据库文件位置

```
H:\毕业设计\System\backend\storage\
└── classinsight.db          # SQLite 数据库文件
```

---

## 8. 模型代码位置

```
H:\毕业设计\System\backend\app\models\
├── __init__.py              # 模型导出
├── user.py                  # 用户模型
├── video.py                 # 视频模型
├── analysis.py              # 分析结果模型
└── schedule.py              # 课程表模型
```

---

## 9. 备份与恢复

### SQLite 备份
```bash
# 备份
cp storage/classinsight.db storage/classinsight_backup_$(date +%Y%m%d).db

# 恢复
cp storage/classinsight_backup_20231219.db storage/classinsight.db
```

### PostgreSQL 备份 (生产环境)
```bash
# 备份
pg_dump classinsight > backup.sql

# 恢复
psql classinsight < backup.sql
```

---

*文档版本: v1.0*  
*最后更新: 2024-12-19*




