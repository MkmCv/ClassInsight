# 管理员页面隐藏实现说明

## ✅ 已实现的功能

### 1. **侧边栏导航按钮控制**

在 `utils.py` 的 `render_sidebar()` 函数中：
- ✅ 根据用户角色（`role`）动态显示/隐藏管理员页面按钮
- ✅ 非管理员用户：只显示通用页面按钮（首页、视频上传、行为分析、教学建议）
- ✅ 管理员用户：额外显示管理员页面按钮（管理员中心、用户管理、课表管理）

### 2. **隐藏 Streamlit 自动生成的页面链接**

Streamlit 会自动扫描 `pages/` 目录并在侧边栏显示所有页面。为了隐藏管理员页面，我们使用了：

#### CSS 隐藏
```css
/* 隐藏管理员页面链接 */
div[data-testid="stSidebarNav"] a[href*="Admin_0"],
div[data-testid="stSidebarNav"] a[href*="5_👤_用户管理"],
div[data-testid="stSidebarNav"] a[href*="6_📅_课表管理"] {
    display: none !important;
}
```

#### JavaScript 动态隐藏
```javascript
// 监听 DOM 变化，确保动态加载的链接也被隐藏
const observer = new MutationObserver(hideAdminPages);
observer.observe(document.body, { childList: true, subtree: true });
```

### 3. **页面级权限检查**

每个管理员页面都有权限检查：
```python
if current_user.get('role') != 'admin':
    st.error("⚠️ 只有管理员可以访问此页面")
    st.stop()
```

即使非管理员用户通过直接输入 URL 访问，也会被阻止。

---

## 🔐 权限控制层次

### 第一层：UI 隐藏
- **侧边栏按钮**：非管理员用户看不到管理员页面按钮
- **Streamlit 自动链接**：通过 CSS + JavaScript 隐藏

### 第二层：页面级检查
- **权限验证**：每个管理员页面都有 `role == 'admin'` 检查
- **自动重定向**：非管理员用户访问时显示错误并阻止

### 第三层：API 权限（后端）
- **JWT Token 验证**：所有 API 请求都需要有效 Token
- **角色检查**：管理员 API 端点会检查用户角色

---

## 📋 管理员页面列表

以下页面仅管理员可见：

1. **`Admin_0_👑_管理员中心.py`** - 管理员仪表盘
2. **`5_👤_用户管理.py`** - 用户管理
3. **`6_📅_课表管理.py`** - 课表管理

---

## 🎯 实现效果

### 对于普通教师用户（`role == 'teacher'`）

**侧边栏显示**：
- 🏠 首页
- 📤 视频上传
- 📈 行为分析
- 💡 教学建议
- 🚪 退出登录

**不显示**：
- ❌ 管理员中心
- ❌ 用户管理
- ❌ 课表管理

### 对于管理员用户（`role == 'admin'`）

**侧边栏显示**：
- 🏠 首页
- 📤 视频上传
- 📈 行为分析
- 💡 教学建议
- ---
- 👑 管理员中心
- 👤 用户管理
- 📅 课表管理
- ---
- 🚪 退出登录

---

## 🔧 技术实现细节

### 1. 动态 CSS 注入

在 `render_sidebar()` 函数中，根据用户角色动态注入 CSS：

```python
if role != 'admin':
    st.markdown("""
    <style>
    /* 隐藏管理员页面链接 */
    ...
    </style>
    <script>
    /* JavaScript 动态隐藏 */
    ...
    </script>
    """, unsafe_allow_html=True)
```

### 2. MutationObserver

使用 `MutationObserver` 监听 DOM 变化，确保 Streamlit 动态加载的页面链接也被隐藏。

### 3. 多重保护

- **前端 UI 隐藏**：用户看不到链接
- **页面级检查**：即使访问也会被阻止
- **API 权限**：后端也会验证权限

---

## ✅ 测试建议

1. **以普通教师身份登录**：
   - 检查侧边栏是否只显示通用页面
   - 检查是否看不到管理员页面链接
   - 尝试直接输入管理员页面 URL，应该被阻止

2. **以管理员身份登录**：
   - 检查侧边栏是否显示所有页面（包括管理员页面）
   - 检查管理员页面是否可以正常访问

---

## 📝 注意事项

1. **Streamlit 自动导航**：Streamlit 会自动在侧边栏显示所有 `pages/` 目录下的页面，所以我们使用 CSS + JavaScript 来隐藏。

2. **直接 URL 访问**：即使隐藏了链接，用户仍可能通过直接输入 URL 访问。页面级的权限检查会阻止这种情况。

3. **缓存问题**：如果修改了权限逻辑，可能需要清除浏览器缓存或重启 Streamlit 服务。

---

## 🚀 后续优化建议

1. **使用 Streamlit 配置**：如果 Streamlit 未来支持基于角色的页面隐藏，可以使用配置文件。

2. **添加日志**：记录非管理员用户尝试访问管理员页面的行为。

3. **更细粒度的权限**：可以添加更多角色（如 `super_admin`、`teacher_admin` 等）。

