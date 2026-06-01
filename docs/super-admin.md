# 超级管理员系统开发指南

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [API 接口](#api-接口)
4. [前端页面](#前端页面)
5. [权限控制](#权限控制)
6. [开发规范](#开发规范)
7. [后续开发计划](#后续开发计划)

---

## 系统概述

### 定位

超级管理员系统是 ClassInsight 的核心管理系统，独立于普通用户系统，专门用于：
- 系统级配置管理（登录安全、模型配置等）
- AI 模型管理（更新、激活、监控）
- 系统维护和监控

### 设计原则

1. **独立系统**：完全独立的 Streamlit 应用，不依赖普通系统
2. **高安全性**：仅超级管理员可访问，严格的权限控制
3. **核心功能**：专注于系统级配置和管理，不涉及业务功能

---

## 架构设计

### 目录结构

```
System/super_admin/
├── app.py                          # 登录页面（主入口）
├── utils.py                        # 工具函数
│   ├── load_css()                 # 加载 CSS 样式
│   ├── render_sidebar()           # 渲染侧边栏
│   └── get_api_headers()          # 获取 API 请求头
└── pages/
    ├── 0_🏠_超级管理员中心.py      # 主页（功能导航）
    ├── 1_🔒_登录安全配置.py       # 登录安全配置
    └── 2_🤖_模型管理.py            # 模型管理
```

### 技术栈

- **前端框架**：Streamlit
- **后端 API**：FastAPI
- **认证方式**：JWT Token
- **数据库**：SQLite（通过 SQLAlchemy ORM）

### 系统启动

```bash
# 进入超级管理员目录
cd "H:\毕业设计\System\System\super_admin"

# 启动应用（使用不同端口避免冲突）
streamlit run app.py --server.port 8502
```

**访问地址**：`http://localhost:8502`

---

## API 接口

### 基础路径

所有超级管理员 API 的基础路径：`/api/v1/super-admin/`

### 认证要求

所有 API 都需要：
- JWT Token（在请求头中：`Authorization: Bearer <token>`）
- 用户角色必须是 `super_admin`

### API 端点列表

#### 1. 登录安全配置

**获取配置**
```
GET /api/v1/super-admin/login-security-config
```

**响应示例**：
```json
{
  "max_login_attempts": 5,
  "lockout_minutes": 15,
  "captcha_required_after": 3,
  "note": "配置修改需要重启服务生效"
}
```

**更新配置**
```
PUT /api/v1/super-admin/login-security-config
```

**请求体**：
```json
{
  "max_login_attempts": 10,
  "lockout_minutes": 30,
  "captcha_required_after": 5
}
```

**响应**：返回修改说明和步骤

#### 2. 模型管理

**获取模型信息**
```
GET /api/v1/super-admin/model-info
```

**响应示例**：
```json
{
  "model_directory": "/path/to/ml/weights",
  "models": [
    {
      "name": "comprehensive_scene_best.pt",
      "path": "/path/to/model.pt",
      "size": 12345678,
      "modified": 1234567890.0
    }
  ],
  "current_config": {
    "model_weights_dir": "/path/to/weights",
    "confidence_threshold": 0.3,
    "nms_iou_threshold": 0.5
  }
}
```

**更新模型**（开发中）
```
POST /api/v1/super-admin/model/update
```

**激活模型**（开发中）
```
POST /api/v1/super-admin/model/activate
```

---

## 前端页面

### 1. 登录页面 (`app.py`)

**功能**：
- 超级管理员登录表单
- 角色验证（仅 `super_admin` 可登录）
- 登录状态管理

**关键代码**：
```python
# 检查是否为超级管理员
if user.get("role") != "super_admin":
    return False, "此账号不是超级管理员"
```

### 2. 超级管理员中心 (`pages/0_🏠_超级管理员中心.py`)

**功能**：
- 系统功能导航
- 快速操作入口
- 系统信息展示

### 3. 登录安全配置 (`pages/1_🔒_登录安全配置.py`)

**功能**：
- 查看当前配置（3个指标卡片）
- 修改配置表单
- 配置说明和最佳实践
- 修改步骤指导

**配置项**：
- `MAX_LOGIN_ATTEMPTS` - 最大登录失败次数
- `LOGIN_LOCKOUT_MINUTES` - 账户锁定时间（分钟）
- `CAPTCHA_REQUIRED_AFTER` - 需要验证码的失败次数

### 4. 模型管理 (`pages/2_🤖_模型管理.py`)

**功能**：
- 查看模型列表（名称、大小、修改时间）
- 查看当前模型配置
- 模型更新（开发中）
- 模型激活（开发中）

---

## 权限控制

### 三级权限结构

```
教师 (teacher)
  └─ 普通系统 (frontend/)
      ├─ 首页
      ├─ 视频上传
      ├─ 行为分析
      └─ 教学建议

管理员 (admin)
  └─ 普通系统 (frontend/)
      ├─ 所有教师功能
      ├─ 用户管理
      ├─ 课表管理
      └─ 登录失败摘要

超级管理员 (super_admin)
  └─ 超级管理员系统 (super_admin/)
      ├─ 登录安全配置
      └─ 模型管理
```

### 权限检查

#### 后端检查

```python
# backend/app/api/v1/endpoints/super_admin.py
async def get_super_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """验证当前用户是否为超级管理员"""
    if current_user.role != UserRole.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有超级管理员可以访问此功能"
        )
    return current_user
```

#### 前端检查

```python
# 登录时检查角色
if user.get("role") != "super_admin":
    return False, "此账号不是超级管理员"

# 页面访问时检查
if current_user.get('role') != 'super_admin':
    st.error("⚠️ 只有超级管理员可以访问此页面")
    st.stop()
```

---

## 开发规范

### 文件命名

- 主文件：`app.py`
- 页面文件：`pages/{序号}_{图标}_{名称}.py`
- 工具文件：`utils.py`

### 路径规范

**Streamlit 页面跳转**：
- 从 `app.py` 跳转到页面：`pages/文件名.py`
- 从 `pages/` 下的文件跳转到 `app.py`：`../app.py`
- 从 `pages/` 下的文件跳转到其他页面：直接使用文件名

**示例**：
```python
# 在 app.py 中
st.switch_page("pages/0_🏠_超级管理员中心.py")

# 在 pages/0_🏠_超级管理员中心.py 中
st.switch_page("../app.py")  # 返回登录页
st.switch_page("1_🔒_登录安全配置.py")  # 跳转到其他页面
```

### API 调用规范

```python
# 使用缓存装饰器
@st.cache_data(ttl=30, show_spinner=False)
def get_data(_headers_tuple):
    headers = dict(_headers_tuple)
    response = requests.get(
        f"{API_BASE_URL}/super-admin/endpoint",
        headers=headers,
        timeout=5
    )
    return response.json() if response.status_code == 200 else None

# 获取请求头
headers_tuple = tuple(get_api_headers().items())
data = get_data(headers_tuple)
```

### 错误处理

```python
try:
    # API 调用
    response = requests.get(...)
    if response.status_code == 200:
        return response.json()
    return None
except Exception as e:
    st.error(f"操作失败: {str(e)}")
    return None
```

---

## 后续开发计划

### 短期（1-2周）

1. **模型管理功能完善**
   - [ ] 模型文件上传
   - [ ] 模型文件验证
   - [ ] 模型版本管理
   - [ ] 模型激活逻辑

2. **配置管理优化**
   - [ ] 动态配置修改（无需重启）
   - [ ] 配置历史记录
   - [ ] 配置回滚功能

### 中期（1-2月）

3. **系统监控**
   - [ ] 系统健康状态监控
   - [ ] 性能指标统计
   - [ ] 错误日志查看

4. **数据管理**
   - [ ] 数据备份与恢复
   - [ ] 数据清理工具
   - [ ] 数据导出功能

### 长期（3-6月）

5. **高级功能**
   - [ ] 多模型 A/B 测试
   - [ ] 模型性能对比
   - [ ] 自动化模型更新
   - [ ] 系统审计日志

---

## 测试指南

### 功能测试

1. **登录测试**
   - ✅ 超级管理员可以登录
   - ✅ 非超级管理员无法登录
   - ✅ 登录后跳转到主页

2. **权限测试**
   - ✅ 超级管理员可以访问所有页面
   - ✅ 普通管理员无法访问超级管理员系统
   - ✅ API 权限检查正常工作

3. **功能测试**
   - ✅ 登录安全配置查看和修改
   - ✅ 模型信息查看
   - ✅ 页面跳转正常

### 性能测试

- API 响应时间 < 1秒
- 页面加载时间 < 2秒
- 并发用户支持（建议 < 10）

---

## 故障排查

### 常见问题

1. **无法登录**
   - 检查账号角色是否为 `super_admin`
   - 检查后端服务是否运行
   - 检查数据库连接

2. **页面跳转失败**
   - 检查路径格式是否正确
   - 检查文件名是否正确
   - 检查 Streamlit 版本

3. **API 调用失败**
   - 检查 Token 是否有效
   - 检查后端服务是否运行
   - 检查网络连接

---

## 参考资料

- [Streamlit 文档](https://docs.streamlit.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [项目 README](../README.md)
- [API 接口文档](./backend/API接口文档.md)

---

## 更新日志

### 2026-01-06
- ✅ 创建超级管理员系统
- ✅ 实现登录安全配置功能
- ✅ 实现模型管理框架
- ✅ 完善权限控制

---

## 联系方式

如有问题或建议，请联系开发团队。

