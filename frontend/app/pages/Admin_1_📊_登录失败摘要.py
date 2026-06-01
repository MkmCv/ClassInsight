"""
登录失败摘要 - 管理员
"""
import streamlit as st
import requests
import sys
import os
from datetime import datetime
import pandas as pd

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, get_api_headers, check_authentication

st.set_page_config(page_title="登录失败摘要 - ClassInsight", page_icon="📊", layout="wide")

load_css()

# ==================== 权限检查 ====================
# 检查登录（自动从 localStorage 恢复）
check_authentication()

render_sidebar()

current_user = st.session_state.get('user', {})
if current_user.get('role') != 'admin':
    st.error("⚠️ 只有管理员可以访问此页面")
    st.stop()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# ==================== 数据获取函数 ====================
@st.cache_data(ttl=10, show_spinner=False)
def get_login_attempts_summary(_headers_tuple):
    """获取登录失败记录摘要"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/admin/login-attempts",
            headers=headers,
            params={"page": 1, "page_size": 50},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "total": data.get("total", 0),
                "items": data.get("items", [])
            }
        return {"total": 0, "items": []}
    except:
        return {"total": 0, "items": []}

# ==================== 页面内容 ====================
st.title("📊 登录失败摘要")

headers_tuple = tuple(get_api_headers().items())
attempts_summary = get_login_attempts_summary(headers_tuple)

# 统计卡片
st.subheader("📈 统计概览")

col1, col2 = st.columns(2)

with col1:
    st.metric("总失败记录数", attempts_summary.get("total", 0))

with col2:
    # 计算当前锁定的账户数
    locked_count = 0
    for item in attempts_summary.get("items", []):
        locked_until = item.get("locked_until")
        if locked_until:
            try:
                lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
                if lock_time > datetime.utcnow():
                    locked_count += 1
            except:
                pass
    st.metric("当前锁定账户数", locked_count)

st.divider()

# 最近失败记录
st.subheader("📋 最近失败记录")

if attempts_summary.get("items"):
    attempts_data = []
    for item in attempts_summary.get("items", [])[:20]:  # 显示最近20条
        locked_until = item.get("locked_until")
        is_locked = False
        lock_time_str = "未锁定"
        
        if locked_until:
            try:
                lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
                is_locked = lock_time > datetime.utcnow()
                if is_locked:
                    lock_time_str = lock_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    lock_time_str = "已解锁"
            except:
                pass
        
        attempts_data.append({
            "用户名": item.get("username", "N/A"),
            "IP地址": item.get("ip_address", "N/A"),
            "失败次数": item.get("failed_count", 0),
            "状态": "🔒 已锁定" if is_locked else "✅ 正常",
            "锁定到期时间": lock_time_str,
            "最后尝试": item.get("last_attempt", "N/A")[:19] if item.get("last_attempt") else "N/A"
        })
    
    if attempts_data:
        df = pd.DataFrame(attempts_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 快速操作
        st.markdown("### 🔧 快速操作")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👤 查看用户管理", use_container_width=True, key="goto_user_mgmt"):
                st.switch_page("pages/5_👤_用户管理.py")
        
        with col2:
            if st.button("🔄 刷新数据", use_container_width=True, key="refresh_attempts"):
                get_login_attempts_summary.clear()
                st.rerun()
else:
    st.info("📭 暂无登录失败记录")

st.divider()

# 说明
st.subheader("ℹ️ 说明")

st.info("""
**功能说明**：

此页面显示系统登录失败记录的摘要信息。如需：

- **查看详细记录**：请前往"用户管理"页面
- **解锁账户**：请在"用户管理"页面中操作
- **配置登录安全参数**：请使用超级管理员系统

**提示**：只有超级管理员可以修改登录安全配置（最大失败次数、锁定时间等）。
""")

