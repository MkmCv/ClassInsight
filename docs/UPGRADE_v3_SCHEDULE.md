# ClassInsight v3 升级说明 - 课表管理与退出登录

## 📋 本次更新内容

### ✅ 后端新增

#### 1. 课表管理API (`/api/v1/schedules`)

| 端点 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/schedules/my` | GET | 教师 | 获取当前教师的所有课程 |
| `/schedules/today` | GET | 教师 | 获取今日课表（首页用） |
| `/schedules/week` | GET | 教师 | 获取周课表（智能日历用） |
| `/schedules/all` | GET | 管理员 | 获取所有课程（可按教师/星期筛选） |
| `/schedules/teachers` | GET | 管理员 | 获取可排课的教师列表 |
| `/schedules` | POST | 管理员 | 创建新课程（排课） |
| `/schedules/{id}` | PUT | 管理员 | 更新课程（调课） |
| `/schedules/{id}` | DELETE | 管理员 | 删除课程 |

#### 2. 新增Schema (`app/schemas/schedule.py`)

- `ScheduleCreate`: 创建课表请求
- `ScheduleUpdate`: 更新课表请求
- `ScheduleResponse`: 课表响应
- `ScheduleWithStatus`: 带状态的课表（finished/ongoing/upcoming）
- `DayScheduleResponse`: 某天的课表响应
- `WeekScheduleResponse`: 周课表响应

---

### ✅ 前端更新

#### 1. 退出登录功能

所有页面侧边栏新增：
- 用户信息展示（用户名 + 角色）
- 🚪 退出登录按钮

影响页面：
- 首页 (`1_🏠_首页.py`)
- 视频上传 (`2_📤_视频上传.py`)
- 行为分析 (`3_📈_行为分析.py`)
- 教学建议 (`4_💡_教学建议.py`)
- 用户管理 (`5_👤_用户管理.py`)
- 课表管理 (`6_📅_课表管理.py`) - 新增

#### 2. 首页智能课表日历

- **日期选择器**: 可选择任意日期查看对应周课表
- **周导航**: 上周/今天/下周快速切换
- **7天视图**: 可视化展示一周课程安排
- **课程状态**: 自动计算并显示（已结束/进行中/待开始）
- **今日课程**: 卡片式展示当天课程

#### 3. 课表管理页面（管理员专用）

路径: `pages/6_📅_课表管理.py`

功能：
- **课表总览**: 7天分栏视图 + 详情列表
- **筛选功能**: 按教师/星期筛选
- **新增课程**: 为教师排课
- **编辑课程**: 调课（修改时间/班级/课程名）
- **删除课程**: 删除课程安排

---

## 🗂️ 文件变更清单

### 后端
```
backend/app/
├── api/v1/
│   ├── router.py           # 新增 schedules 路由
│   └── endpoints/
│       └── schedules.py    # 新增 课表管理API
└── schemas/
    ├── __init__.py         # 导出 schedule schemas
    └── schedule.py         # 新增 课表相关Schema
```

### 前端
```
System/frontend/
├── utils.py                # 新增 render_sidebar(), get_api_headers()
└── pages/
    ├── 1_🏠_首页.py        # 智能日历 + 侧边栏
    ├── 2_📤_视频上传.py    # 侧边栏
    ├── 3_📈_行为分析.py    # 侧边栏
    ├── 4_💡_教学建议.py    # 侧边栏
    ├── 5_👤_用户管理.py    # 侧边栏 + 启用后端API
    └── 6_📅_课表管理.py    # 新增 管理员排课页面
```

---

## 🚀 启动说明

### 后端
```bash
cd backend
python run.py
```

### 前端
```bash
cd System/frontend
streamlit run app.py
```

---

## 📌 测试要点

1. **退出登录**
   - 点击侧边栏「退出登录」按钮
   - 应清除session并跳转登录页

2. **智能日历**
   - 首页选择不同日期，查看对应周课表
   - 课程状态应根据当前时间自动计算

3. **排课功能（管理员）**
   - 进入课表管理页面
   - 创建新课程，检查时间冲突提示
   - 编辑/删除课程

4. **教师查看课表**
   - 普通教师登录后，首页应显示其课表
   - 无法访问课表管理页面（权限限制）

---

## 📅 更新日期
2025-01-07

















