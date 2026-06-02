# ClassInsight 数据库说明

## 1. 使用什么数据库

- **默认**：**SQLite** 单文件数据库，路径由配置中的 `DATABASE_URL` 决定。
- **访问方式**：**SQLAlchemy 2.x 异步 ORM** + **`aiosqlite`**（异步驱动）。
- **物理文件**（默认、与 README 一致）：`backend/storage/classinsight.db`。

特点：单机部署、免独立数据库服务；生产环境如需更强并发可更换为 PostgreSQL 等，主要改连接串与驱动。

---

## 2. 数据库是如何「搭建」的

本项目**不依赖单独的一次性 SQL 脚本**完成首次建库，而是：

1. **配置**：`backend/app/core/config.py` 中 `DATABASE_URL`，例如  
   `sqlite+aiosqlite:///./storage/classinsight.db`。

2. **引擎与会话**：`backend/app/core/database.py`  
   - `create_async_engine` 创建连接池；  
   - 对 SQLite 连接设置 `PRAGMA foreign_keys=ON`、`busy_timeout`，保证外键与并发写更稳；  
   - `AsyncSessionLocal` 供业务 `Depends(get_db)` 使用。

3. **建表**：`init_db()` 中 **先 `import ..models` 注册所有 ORM**，再对 `Base.metadata` 执行 **`create_all`**。  
   - **效果**：表若不存在则创建；**不会**自动删除或大幅变更已有表结构。  
   - **结构演进**：如需补列/补表，可编写一次性迁移脚本手工执行。

4. **触发时机**：`backend/main.py` 里 FastAPI **`lifespan`** 在应用启动时 **`await init_db()`**，因此**启动后端即完成（或补齐）表结构**。

---

## 3. 表一览与职责

| 表名 | 说明 |
|------|------|
| `users` | 用户：用户名、邮箱、密码哈希、角色（teacher/admin/super_admin）、单位、班级、`is_active` 等。 |
| `videos` | 视频：归属用户、文件路径与大小、元数据（时长/fps/分辨率）、课程信息、处理状态与进度等。 |
| `analysis_timeline` | 时间线：按时间窗存储行为计数（JSON）、可选检测框快照；一行对应一个 `(video_id, 窗起点秒, window_size)`。 |
| `analysis_summary` | 整课汇总：每视频通常一行；`summary_json`（JSON）及互动率、专注度、参与度等标量；**规则化教学建议**主要读此表。 |
| `analysis_anomalies` | 异常时段：起止时间、类型、严重程度、描述及相关统计 JSON。 |
| `schedules` | 课表：教师、课程名、班级、星期、起止时间等。 |
| `verification_codes` | 邮箱验证码：用途、过期时间、是否已使用。 |
| `login_attempts` | 登录风控：用户名+IP 维度失败次数、锁定截止时间等。 |
| `login_history` | 登录审计：成功/失败、用户（可空）、IP、UA、时间等。 |

模型定义目录：`backend/app/models/`；聚合导出：`backend/app/models/__init__.py`。

---

## 4. 核心表关系（课堂分析主线）

```
users
  ├── videos (user_id)
  │     ├── analysis_timeline (video_id)
  │     ├── analysis_summary (video_id, 1:1)
  │     └── analysis_anomalies (video_id)
  └── schedules (user_id)
```

- 视频与分析子表多为 **`ondelete="CASCADE"`**：删视频会删掉对应时间线/汇总/异常（具体以外键定义为准）。  
- `login_history.user_id` 对用户删除多为 **`SET NULL`**，便于保留审计。

---

## 5. 与业务模块的对应

| 模块 | 主要涉及的表 |
|------|----------------|
| 注册 / 登录 / JWT | `users`、`login_attempts`、`login_history` |
| 忘记密码 / 验证码 | `verification_codes`、`users` |
| 视频上传与处理 | `videos` → 写 `analysis_*` |
| 行为分析 API、图表 | `analysis_timeline`、`analysis_summary`、`analysis_anomalies` |
| 教学建议（规则） | `analysis_summary`（`summary_json`） |
| AI 顾问上下文 | `analysis_summary`、时间线、异常（经 `agent/tools` 读取） |
| 课表 / 首页日历 | `schedules`、`users` |

---

## 6. 代码索引

| 内容 | 路径 |
|------|------|
| 连接串与存储路径 | `backend/app/core/config.py` |
| 引擎、`init_db`、`get_db` | `backend/app/core/database.py` |
| 启动时初始化 | `backend/main.py`（`lifespan`） |
| ORM 模型 | `backend/app/models/*.py` |

---

## 7. 常见问题速答

**Q：数据库怎么建的？**  
A：SQLite 单文件，SQLAlchemy 模型描述表结构，**服务启动时 `create_all` 自动建表**。

**Q：为什么用 SQLite？**  
A：部署简单、与 Python 栈集成方便；若要并发与复杂运维可换 PostgreSQL，只需改 `DATABASE_URL`。

**Q：分析结果存在哪？**  
A：**时间序列**在 `analysis_timeline`，**整课统计与建议依据**在 `analysis_summary`，**异常片段**在 `analysis_anomalies`。
