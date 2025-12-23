# 👤 用户管理页面 - 前端对接规范

## 1. 页面概述

| 属性 | 值 |
|------|-----|
| **文件路径** | `pages/5_👤_用户管理.py` |
| **访问权限** | 仅管理员 (role = "admin") |
| **功能** | 用户列表、创建用户、删除用户、重置密码 |

---

## 2. 权限控制

页面加载时必须验证用户角色：

```python
current_user = st.session_state.get('user', {})
if current_user.get('role') != 'admin':
    st.error("⚠️ 只有管理员可以访问此页面")
    st.stop()
```

---

## 3. API 接口

### 3.1 获取用户列表

| 属性 | 值 |
|------|-----|
| **接口** | `GET /api/v1/admin/users` |
| **权限** | Admin |
| **参数** | `page` (页码), `page_size` (每页数量), `role` (可选筛选) |

**响应示例**：
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "unit": "系统管理",
    "class_name": null,
    "created_at": "2025-01-01T00:00:00"
  },
  {
    "id": 2,
    "username": "teacher001",
    "email": "teacher@example.com",
    "role": "teacher",
    "unit": "数学系",
    "class_name": "高一(1)班",
    "created_at": "2025-10-23T10:00:00"
  }
]
```

---

### 3.2 创建用户

| 属性 | 值 |
|------|-----|
| **接口** | `POST /api/v1/auth/register` |
| **权限** | 公开（但管理员可用于批量创建） |

**请求体**：
```json
{
  "username": "teacher002",
  "email": "teacher2@school.edu",
  "password": "12345678",
  "role": "teacher",
  "unit": "数学系",
  "class_name": "高一(2)班"
}
```

**字段验证规则**：
| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| username | string | ✅ | 3-50字符，唯一 |
| email | string | ✅ | 有效邮箱格式，唯一 |
| password | string | ✅ | **至少8位** |
| role | string | ❌ | "teacher" 或 "admin"，默认 "teacher" |
| unit | string | ❌ | 最大100字符 |
| class_name | string | ❌ | 最大50字符 |

**响应**：
- `201 Created`: `{"user_id": 3, "username": "teacher002", "message": "注册成功"}`
- `409 Conflict`: `{"detail": "用户名已存在"}` 或 `{"detail": "邮箱已被注册"}`
- `422 Unprocessable Entity`: 字段验证失败

---

### 3.3 删除用户

| 属性 | 值 |
|------|-----|
| **接口** | `DELETE /api/v1/admin/users/{user_id}` |
| **权限** | Admin |

**响应**：
- `200 OK`: `{"message": "用户已删除"}`
- `400 Bad Request`: `{"detail": "不能删除自己"}`
- `404 Not Found`: `{"detail": "用户不存在"}`

---

### 3.4 重置用户密码

| 属性 | 值 |
|------|-----|
| **接口** | `POST /api/v1/admin/users/{user_id}/reset-password` |
| **权限** | Admin |
| **参数** | `new_password` (Query 参数，至少8位) |

**请求示例**：
```
POST /api/v1/admin/users/2/reset-password?new_password=newpass123
```

**响应**：
- `200 OK`: `{"message": "密码已重置"}`
- `404 Not Found`: `{"detail": "用户不存在"}`

---

### 3.5 获取系统统计

| 属性 | 值 |
|------|-----|
| **接口** | `GET /api/v1/admin/statistics` |
| **权限** | Admin |

**响应示例**：
```json
{
  "users": {
    "total": 10,
    "teachers": 8,
    "admins": 2
  },
  "videos": {
    "total": 50,
    "completed": 45,
    "processing": 3,
    "failed": 2
  },
  "analyses": {
    "total": 45
  }
}
```

---

### 3.6 获取所有视频（管理员）

| 属性 | 值 |
|------|-----|
| **接口** | `GET /api/v1/admin/videos` |
| **权限** | Admin |
| **参数** | `page`, `page_size`, `status` (可选) |

**响应示例**：
```json
{
  "total": 50,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "video_id": 1,
      "user_id": 2,
      "filename": "class_math.mp4",
      "class_name": "高一(1)班",
      "course_name": "数学",
      "lesson_date": "2025-10-23",
      "status": "completed",
      "duration": 2700,
      "created_at": "2025-10-23T10:00:00"
    }
  ]
}
```

---

### 3.7 删除任意视频（管理员）

| 属性 | 值 |
|------|-----|
| **接口** | `DELETE /api/v1/admin/videos/{video_id}` |
| **权限** | Admin |

**响应**：
- `200 OK`: `{"message": "视频已删除"}`
- `404 Not Found`: `{"detail": "视频不存在"}`

---

## 4. UI 组件规范

### 4.1 用户选择器

**不要使用**：手动输入 ID 的数字输入框

**应该使用**：下拉选择器，显示格式：

```
用户名 (ID: x) - 角色
```

**示例代码**：
```python
user_options = {
    u['id']: f"{u.get('username')} (ID: {u['id']}) - {u.get('role')}"
    for u in users
}

selected_user_id = st.selectbox(
    "选择用户",
    options=list(user_options.keys()),
    format_func=lambda x: user_options[x]
)
```

### 4.2 删除确认

**必须**：在执行删除前显示确认对话框

```python
if st.session_state.get('confirm_delete') == user_id:
    st.warning(f"⚠️ 确定要删除用户吗？此操作不可撤销！")
    if st.button("✅ 确认删除"):
        # 执行删除
    if st.button("❌ 取消"):
        st.session_state['confirm_delete'] = None
```

### 4.3 密码重置表单

**必须验证**：
- 新密码至少 8 位
- 确认密码与新密码一致

---

## 5. 错误处理

所有 API 调用必须包含错误处理：

```python
try:
    response = requests.get(url, headers=get_api_headers(), timeout=5)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        st.error("权限不足")
    elif response.status_code == 404:
        st.error("资源不存在")
    else:
        try:
            error_msg = response.json().get("detail", "请求失败")
        except:
            error_msg = f"请求失败 (HTTP {response.status_code})"
        st.error(error_msg)
except requests.exceptions.ConnectionError:
    st.error("无法连接到服务器")
except requests.exceptions.Timeout:
    st.error("请求超时")
```

---

## 6. 开发/生产切换

```python
# 开发模式：使用 Mock 数据
USE_BACKEND_API = False

# 生产模式：使用真实 API
USE_BACKEND_API = True
```

---

## 7. Mock 数据位置

```
frontend/mock_data.py
```

包含 `MOCK_USERS_LIST` 用于开发测试。

---

## 8. 测试检查清单

- [ ] 非管理员用户无法访问页面
- [ ] 用户列表正确显示所有用户
- [ ] 创建用户：密码少于8位时报错
- [ ] 创建用户：用户名重复时报错
- [ ] 删除用户：不能删除自己
- [ ] 删除用户：需要确认才能删除
- [ ] 重置密码：两次密码必须一致
- [ ] 重置密码：密码至少8位

---

*文档版本: v1.0*  
*最后更新: 2025-12-19*




