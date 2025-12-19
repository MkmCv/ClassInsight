# 🔄 后端交接文档 v1.2 (Backend Handoff)

**日期**: 2025-12-19  
**版本**: v1.2  
**状态**: 核心功能已实现

本文档基于前端开发的最新进展，汇总了后端需要实现的具体接口变更、新增模块以及注意事项。

---

## 📋 变更记录

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.2 | 2025-12-19 | 前端视频删除功能已实现 |
| v1.1 | 2025-12-19 | 新增行为分析图表说明、管理员API已实现 |
| v1.0 | 2025-12-19 | 初始版本 |

---

## 1. 用户管理模块 ✅ 已实现

前端已新增 `pages/5_👤_用户管理.py` 页面，仅 **Admin** 角色可访问。

### 1.1 API 实现状态

| 接口 | 方法 | 路径 | 状态 |
|------|------|------|------|
| 获取用户列表 | GET | `/api/v1/admin/users` | ✅ 已实现 |
| 获取用户详情 | GET | `/api/v1/admin/users/{id}` | ✅ 已实现 |
| 更新用户信息 | PUT | `/api/v1/admin/users/{id}` | ✅ 已实现 |
| 删除用户 | DELETE | `/api/v1/admin/users/{id}` | ✅ 已实现 |
| 重置密码 | POST | `/api/v1/admin/users/{id}/reset-password` | ✅ 已实现 |
| 系统统计 | GET | `/api/v1/admin/statistics` | ✅ 已实现 |
| 所有视频 | GET | `/api/v1/admin/videos` | ✅ 已实现 |
| 删除视频 | DELETE | `/api/v1/admin/videos/{id}` | ✅ 已实现 |

### 1.2 后端代码位置
- **路由文件**: `backend/app/api/v1/endpoints/admin.py`
- **权限依赖**: `get_admin_user()` 函数验证管理员权限

### 1.3 前端切换到真实 API
```python
# pages/5_👤_用户管理.py 第 30 行
USE_BACKEND_API = True  # 改为 True 启用后端 API
```

---

## 2. 行为分析页面重构 ✅ 已完成

前端 `pages/3_📈_行为分析.py` 的 Tab 2（课堂趋势）已重新设计。

### 2.1 新增图表

| 图表名称 | 说明 | 数据来源 |
|---------|------|---------|
| **教学模式时间线** | 用颜色方块展示每个时段的教学活动类型 | timeline API |
| **教学模式占比饼图** | 各模式的时间占比 | timeline API |
| **互动强度曲线** | 基于互动行为计算的 0-100 指数 | timeline API |
| **教学丰富度曲线** | 使用了多少种教学方式 | timeline API |
| **教学行为热力图** | 真正的热力图，颜色深浅表示频率 | timeline API |

### 2.2 教学模式分类逻辑

```python
def get_teaching_mode(row):
    # 互动模式：有引导、回答或上台互动
    interaction = row.get('guide', 0) + row.get('answer', 0) + row.get('On-stage interaction', 0)
    # 板书模式：有板书行为
    blackboard = row.get('blackboard-writing', 0)
    # 多媒体模式：屏幕活跃
    multimedia = row.get('screen', 0)
    # 讲授模式：教师站立
    lecture = row.get('teacher', 0) + row.get('stand', 0)
    
    if interaction > 0:
        return "🗣️ 互动教学"      # 绿色 #10B981
    elif blackboard > 0:
        return "✏️ 板书讲解"       # 蓝色 #3B82F6
    elif multimedia > 0:
        return "🖥️ 多媒体演示"     # 紫色 #8B5CF6
    elif lecture > 0:
        return "👨‍🏫 讲授模式"       # 橙色 #F59E0B
    else:
        return "⏸️ 其他"          # 灰色 #9CA3AF
```

### 2.3 互动指数计算公式

```python
互动指数 = guide × 30 + answer × 25 + On-stage_interaction × 45
# 最高 100 分，超过则截断
```

| 指数范围 | 评价 |
|---------|------|
| 50+ | 优秀互动 |
| 30-50 | 良好 |
| 10-30 | 一般 |
| <10 | 需提升 |

### 2.4 教学丰富度计算

```python
def calc_richness(row):
    methods = 0
    if teacher/stand > 0: methods += 1    # 讲授
    if blackboard-writing > 0: methods += 1  # 板书
    if screen > 0: methods += 1            # 多媒体
    if guide/answer > 0: methods += 1      # 互动
    return methods * 25  # 最高 100
```

---

## 3. 模型检测能力说明

### 3.1 当前模型运行状态

| 模型 | 权重文件 | 状态 | 检测类别 | 数据类型 |
|------|----------|------|----------|----------|
| **comprehensive** | `comprehensive_scene_best.pt` | ✅ **运行中** | 8类 | 🔵 **真实检测** |
| learning | `student_learning_best.pt` | ⏳ 待放置 | 3类 | 🟡 Mock 模拟 |
| discussion | `student_discussion_best.pt` | ⏳ 待放置 | 1类 | 🟡 Mock 模拟 |
| posture | `student_posture_best.pt` | ⏳ 待放置 | 2类 | 🟡 Mock 模拟 |

### 3.2 🔵 comprehensive_scene 已识别类别（真实数据）

**模型已成功加载并产生真实检测结果！** 以下是最近一次视频分析的检测数据：

| 类别 | 中文 | 全局ID | 检测次数 | 用途 |
|------|------|--------|---------|------|
| `teacher` | 教师 | 10 | 2147次 ✅ | 教学模式判断 |
| `guide` | 引导 | 7 | 180次 ✅ | 互动指数计算 |
| `stand` | 站立 | 12 | 97次 ✅ | 教学模式判断 |
| `answer` | 回答 | 8 | - | 互动指数计算 |
| `On-stage interaction` | 上台互动 | 9 | - | 互动指数计算 |
| `blackboard-writing` | 板书 | 11 | - | 教学模式判断 |
| `screen` | 屏幕 | 13 | - | 教学模式判断 |
| `blackBoard` | 黑板 | 14 | - | 场景元素 |

> 💡 **注意**: `teacher`, `guide`, `stand` 等类别已有真实检测数据，其他类别取决于视频内容是否出现对应场景。

### 3.3 🟡 待放置模型的类别（Mock 模拟数据）

以下类别目前使用 **模拟数据**，待放置对应模型后将转为真实检测：

| 模型 | 类别 | Mock 检测次数示例 |
|------|------|------------------|
| learning | `hand-raising`, `read`, `write` | 602 / 1892 / 1827 |
| discussion | `discuss` | 888 |
| posture | `BowHead`, `TurnHead` | 303 / - |

### 3.4 数据混合策略

当前系统采用 **真实 + Mock 混合** 策略：
1. ✅ `comprehensive` 模型 → 真实 YOLO 推理结果
2. 🟡 其他未加载模型 → `generate_mock_detections()` 生成模拟数据
3. 前端统一处理，无需区分数据来源

---

## 4. 视频接口更新

### 4.1 上传接口字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | Binary | ✅ | 视频文件 |
| `class_name` | String | ❌ | 班级名称 |
| `course_name` | String | ❌ | 课程名称 |
| `lesson_date` | String | ❌ | 上课日期 (YYYY-MM-DD) |
| `teacher_name` | String | ❌ | 授课教师 (新增) |

### 4.2 删除视频接口 ✅ 前端已实现

前端在 `pages/2_📤_视频上传.py` 已实现完整的删除功能。

#### 前端实现细节
| 功能 | 实现状态 |
|------|---------|
| 删除按钮 (🗑️) | ✅ 每行视频右侧 |
| 确认对话框 | ✅ 防止误删 |
| 删除成功提示 | ✅ 自动刷新列表 |
| 错误处理 | ✅ 显示失败原因 |

#### 后端 API ✅ 已实现
- **Path**: `/api/v1/videos/{video_id}`
- **Method**: `DELETE`
- **代码位置**: `backend/app/api/v1/endpoints/videos.py` 第 248-281 行
- **返回**: `204 No Content`（前端已兼容 200/204）
- **权限**: Teacher 只能删除自己上传的视频
- **实现逻辑**:
    - ✅ 验证当前用户是否有权限操作该视频
    - ✅ 物理删除视频文件
    - ✅ 删除数据库记录（级联删除关联数据）

---

## 5. 鉴权与安全

### 5.1 角色定义
- `admin`: 系统管理员，拥有所有权限
- `teacher`: 普通用户，仅能管理自己的视频

### 5.2 权限校验
```python
# backend/app/api/v1/endpoints/admin.py
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
```

---

## 6. 数据库初始化

建议在后端启动时自动创建默认管理员账号：

```python
# 默认管理员
username = "admin"
password = "admin123"  # 建议首次登录强制修改
role = "admin"
```

---

## 7. 待实现功能

| 功能 | 优先级 | 状态 |
|------|--------|------|
| 课程表 CRUD API | 中 | ⏳ 待实现 |
| 归因分析真实计算 | 低 | ⏳ 返回模拟数据 |
| 精彩片段识别 | 低 | ⏳ 返回模拟数据 |
| AI Agent 接入 | 中 | ⏳ 待设计 |
| PDF 报告导出 | 低 | ⏳ 待实现 |

---

## 8. 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 前端 Mock 数据 | `System/frontend/mock_data.py` | API 响应参考模版 |
| 前端接口定义 | `docs/frontend/FRONTEND_INTERFACE.md` | 详细字段定义 |
| 管理页面规范 | `docs/frontend/ADMIN_PAGE_SPEC.md` | UI 交互逻辑 |
| 数据库设计 | `docs/backend/DATABASE_DESIGN.md` | ER 图和表结构 |
| 数据集与模型 | `docs/references/数据集与模型总结.md` | 模型能力说明 |

---

## 9. 检查工具

### 查看分析数据
```powershell
cd "H:\毕业设计\System\backend"
python check_analysis_data.py
```

### 查看已加载模型
```powershell
python -c "from app.ml.detector import MultiModelDetector; d = MultiModelDetector(); print(d.get_model_info())"
```

---

*请在开发过程中，若发现接口无法满足需求，及时更新此文档并通知前端。*
