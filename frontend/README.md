# 前端（Streamlit）

ClassInsight 的前端由两套独立的 Streamlit 多页应用组成，均通过 HTTP + JWT 调用后端 FastAPI（默认 `http://localhost:8000`）。

## 目录

| 子项目 | 说明 | 默认端口 |
|--------|------|---------|
| [`app/`](app/) | 教师 / 管理员端：首页、视频上传、行为分析、教学建议、课表管理、用户管理、管理员中心 | `8501` |
| [`super_admin/`](super_admin/) | 超级管理员端：超级管理员中心、登录安全配置、模型管理 | `8502` |

```
frontend/
├── app/
│   ├── app.py            # 入口
│   ├── pages/            # 各功能页（按文件名排序）
│   ├── utils.py          # API 调用、会话、通用组件
│   └── .streamlit/       # 主题与服务配置
└── super_admin/
    ├── app.py
    ├── pages/
    └── utils.py
```

## 运行

> 需先启动后端服务（见 [`../backend`](../backend)）。建议在 CMD 中先激活 Conda 环境。

```bash
# 教师 / 管理员端 -> http://localhost:8501
cd frontend/app
streamlit run app.py

# 超级管理员端 -> http://localhost:8502
cd frontend/super_admin
streamlit run app.py --server.port 8502
```

## 说明

- 后端地址在各自的 `utils.py` 中配置（默认 `http://localhost:8000`）。
- 前端对部分接口有约 60 秒缓存，修改后端数据后可能需要等待或刷新。
- 运行时产生的 `temp_sessions/`、`last_login.json` 为本地会话状态，不纳入版本控制。
- 更多界面与交互说明见 [`../docs/frontend/`](../docs/frontend/)。
