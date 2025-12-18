# 🎓 ClassInsight Backend

课堂行为分析系统后端服务

## 📁 项目结构

```
backend/
├── app/                        # 应用代码
│   ├── api/                    # API 路由
│   │   ├── deps.py             # 依赖注入
│   │   └── v1/                 # API v1 版本
│   │       ├── router.py       # 路由聚合
│   │       └── endpoints/      # 各模块端点
│   │           ├── auth.py     # 认证
│   │           ├── dashboard.py # 首页
│   │           ├── videos.py   # 视频管理
│   │           ├── analysis.py # 行为分析
│   │           └── optimization.py # 教学优化
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 应用配置
│   │   ├── database.py         # 数据库连接
│   │   └── security.py         # 安全相关
│   ├── models/                 # 数据库模型
│   │   ├── user.py             # 用户模型
│   │   ├── video.py            # 视频模型
│   │   ├── analysis.py         # 分析结果模型
│   │   └── schedule.py         # 课程表模型
│   ├── schemas/                # Pydantic 模式
│   │   ├── user.py             # 用户相关
│   │   ├── video.py            # 视频相关
│   │   ├── analysis.py         # 分析相关
│   │   └── optimization.py     # 优化相关
│   ├── services/               # 业务服务
│   │   └── video_processor.py  # 视频处理服务
│   └── ml/                     # 机器学习模块
│       ├── detector.py         # YOLO-vHeat 检测器
│       └── weights/            # 模型权重 ← 放置训练好的模型
├── storage/                    # 文件存储
│   └── videos/                 # 上传的视频
├── main.py                     # 应用入口
├── run.py                      # 启动脚本
├── requirements.txt            # Python 依赖
└── .env.example                # 环境变量示例
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 激活 conda 环境
conda activate vHeat

# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
copy .env.example .env

# 编辑 .env 文件，修改必要的配置
```

### 3. 放置模型权重

将训练好的模型权重文件放置到 `ml/weights/` 目录：

```
ml/weights/
├── comprehensive_scene_best.pt
├── student_learning_best.pt
├── student_discussion_best.pt
└── student_posture_best.pt
```

### 4. 启动服务

```bash
# 方式1：使用启动脚本
python run.py

# 方式2：使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API

- API 文档 (Swagger): http://localhost:8000/api/docs
- ReDoc 文档: http://localhost:8000/api/redoc
- 健康检查: http://localhost:8000/health

## 📋 API 模块

### 认证模块 `/api/v1/auth`
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户信息
- `PUT /password` - 修改密码

### 首页模块 `/api/v1/dashboard`
- `GET /schedule` - 获取今日课程表
- `GET /metrics` - 获取核心指标
- `GET /recent-videos` - 获取最近视频

### 视频管理 `/api/v1/videos`
- `POST /upload` - 上传视频
- `GET /` - 获取视频列表
- `GET /{video_id}` - 获取视频详情
- `GET /{video_id}/status` - 查询处理状态
- `DELETE /{video_id}` - 删除视频

### 行为分析 `/api/v1/analysis`
- `GET /{video_id}/summary` - 整课统计汇总
- `GET /{video_id}/timeline` - 时间序列数据
- `GET /{video_id}/anomalies` - 异常时段
- `GET /{video_id}/causation` - 行为成因分析

### 教学优化 `/api/v1/optimization`
- `GET /{video_id}/radar` - 雷达图数据
- `GET /{video_id}/recommendations` - 优化建议
- `GET /{video_id}/highlights` - 优秀片段
- `GET /compare` - 跨课次对比

## 🔧 开发说明

### 数据库迁移

项目使用 SQLAlchemy 的自动创建表功能。首次启动时会自动创建所有表。

如需手动管理迁移，可以引入 Alembic。

### 模型集成

检测器位于 `app/ml/detector.py`，封装了4个YOLO-vHeat模型：
- `comprehensive_scene` - 综合场景检测
- `student_learning` - 学习行为检测
- `student_discussion` - 讨论行为检测
- `student_posture` - 姿态检测

### 全局类别ID映射

```python
GLOBAL_CATEGORY_MAPPING = {
    'BowHead': 1, 'TurnHead': 2,           # 姿态
    'hand-raising': 3, 'read': 4, 'write': 5,  # 学习
    'discuss': 6,                           # 讨论
    'guide': 7, 'answer': 8, 'On-stage interaction': 9,
    'teacher': 10, 'blackboard-writing': 11, 'stand': 12,
    'screen': 13, 'blackBoard': 14          # 综合
}
```

## 📝 注意事项

1. **开发环境**：默认使用 SQLite，生产环境建议切换到 PostgreSQL
2. **模型加载**：首次请求时会加载模型，可能需要几秒钟
3. **视频处理**：大视频处理时间较长，使用后台任务异步处理
4. **CORS 配置**：确保前端地址在 CORS_ORIGINS 列表中

## 🔗 相关文档

- [后端需求规格](../docs/backend/BACKEND_REQUIREMENTS.md)
- [API 接口文档](../docs/backend/API接口文档.md)
- [数据集与模型总结](../docs/references/数据集与模型总结.md)

