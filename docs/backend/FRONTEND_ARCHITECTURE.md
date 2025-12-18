# 🏗️ 前端架构与扩展指南 (Frontend Architecture & Development Guide)

本文档旨在为 "ClassInsight" 前端项目提供架构说明、目录结构解释及扩展开发指南，以确保代码库的高可维护性、健壮性和可拓展性。

## 1. 技术栈

- **框架**: Streamlit (Python)
- **图表库**: Plotly Express / Graph Objects
- **样式**: Custom CSS + HTML Injection
- **数据处理**: Pandas

---

## 2. 目录结构说明

```text
System/frontend/
├── app.py                  # [入口] 应用主入口，负责全局配置、登录逻辑、路由分发
├── style.css               # [样式] 全局 CSS 文件，定义配色、卡片、侧边栏样式
├── utils.py                # [工具] 通用工具函数（如 load_css, auth_check）
├── mock_data.py            # [数据] 开发阶段的模拟数据源，结构与后端 API 保持一致
├── pages/                  # [页面] Streamlit 多页面应用目录
│   ├── 1_🏠_首页.py        # 综合工作台（Dashboard）
│   ├── 2_📤_视频上传.py    # 视频上传与进度展示
│   ├── 3_📈_行为分析.py    # 核心分析报表
│   └── 4_💡_教学建议.py    # 改进建议与 AI 助手
└── assets/                 # [资源] 静态图片等（可选）
```

### 关键设计决策
1.  **app.py 作为守门人**: `app.py` 实际上是一个“登录页”。一旦认证成功，它会重定向到 `pages/1_🏠_首页.py`。
2.  **utils.py 统一管理**: 所有页面必须通过 `utils.load_css()` 加载样式，确保 UI 风格统一。
3.  **Mock 数据分离**: 所有模拟数据都封装在 `mock_data.py` 中，页面只负责调用获取数据的函数（如 `get_mock_summary`），不包含硬编码的数据字典。这为以后替换为 API 调用提供了便利。

---

## 3. 开发规范与最佳实践

### 3.1 状态管理 (Session State)
Streamlit 是无状态的，我们使用 `st.session_state` 来持久化跨页面的数据。
- `st.session_state['authentication_status']`: (bool) 是否已登录
- `st.session_state['user']`: (dict) 当前用户信息
- `st.session_state['current_video_id']`: (int) 当前分析的视频 ID（可选）

### 3.2 样式注入
不要在页面文件中直接写 `<style>...</style>`。
**正确做法**: 修改 `style.css`，然后由 `utils.load_css()` 自动注入。

### 3.3 路径处理
为了兼容不同操作系统和运行目录，所有文件读取（如 CSS、图片）都必须使用 `os.path.abspath` 和 `os.path.join`，禁止使用硬编码的相对路径（如 `"./style.css"`）。

**示例**:
```python
# utils.py
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "style.css")
```

---

## 4. 如何扩展新功能

### 场景 A: 添加一个新的分析页面
1.  在 `pages/` 目录下创建一个新文件，例如 `5_📊_深度统计.py`。
2.  复制以下模板代码：
    ```python
    import streamlit as st
    import sys
    import os
    
    # 路径修复
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_css
    
    st.set_page_config(page_title="深度统计", layout="wide")
    load_css()
    
    # 鉴权
    if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
        st.switch_page("app.py")
        
    st.markdown("# 新页面标题")
    ```
3.  实现业务逻辑。

### 场景 B: 对接真实后端 API
目前项目使用 `mock_data.py`。对接真实后端时：
1.  创建一个新的文件 `api_client.py`。
2.  在其中编写函数，使用 `requests` 库调用后端接口。
    ```python
    # api_client.py
    import requests
    
    def get_summary(video_id):
        # 替换 get_mock_summary
        resp = requests.get(f"/api/v1/analysis/{video_id}/summary")
        return resp.json()
    ```
3.  在页面文件中，将 `from mock_data import get_mock_summary` 替换为 `from api_client import get_summary`。

---

## 5. 健壮性维护

1.  **异常处理**: API 调用应包含 `try-except` 块，处理网络超时或 500 错误，并使用 `st.error()` 友好提示用户。
2.  **空数据处理**: 在渲染图表前，检查 DataFrame 是否为空，避免 Plotly 报错。
3.  **布局自适应**: 尽量使用 `st.columns` 和 `use_container_width=True`，确保在不同屏幕宽度下表现良好。
