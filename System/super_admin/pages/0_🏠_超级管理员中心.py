"""
超级管理员中心
"""
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, get_api_headers

st.set_page_config(page_title="超级管理员中心 - ClassInsight", page_icon="🏠", layout="wide")

load_css()

# ==================== 权限检查 ====================
if 'super_admin_auth' not in st.session_state or not st.session_state['super_admin_auth']:
    st.warning("请先登录")
    st.switch_page("../app.py")

render_sidebar()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.title("🏠 超级管理员中心")

st.markdown("""
<div style="padding: 1.5rem; background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); 
            border-radius: 12px; color: white; margin-bottom: 2rem;">
    <h2 style="color: white; margin: 0;">🔐 系统管理</h2>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">管理 ClassInsight 系统的核心配置和模型</p>
</div>
""", unsafe_allow_html=True)

# 功能卡片
st.subheader("🚀 系统功能")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="padding: 1.5rem; border: 2px solid #E5E7EB; border-radius: 12px; height: 200px;">
        <h3 style="color: #111827; margin-top: 0;">🔒 登录安全配置</h3>
        <p style="color: #6B7280;">配置系统登录安全参数：</p>
        <ul style="color: #6B7280;">
            <li>最大登录失败次数</li>
            <li>账户锁定时间</li>
            <li>验证码触发条件</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("前往配置", use_container_width=True, key="goto_security"):
        st.switch_page("pages/1_🔒_登录安全配置.py")

with col2:
    st.markdown("""
    <div style="padding: 1.5rem; border: 2px solid #E5E7EB; border-radius: 12px; height: 200px;">
        <h3 style="color: #111827; margin-top: 0;">🤖 模型管理</h3>
        <p style="color: #6B7280;">管理系统 AI 模型：</p>
        <ul style="color: #6B7280;">
            <li>查看模型信息</li>
            <li>更新模型版本</li>
            <li>激活最新模型</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("前往管理", use_container_width=True, key="goto_model"):
        st.switch_page("pages/2_🤖_模型管理.py")

st.divider()

# 系统信息
st.subheader("ℹ️ 系统信息")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.info("""
    **系统版本**: ClassInsight v1.0.0
    
    **超级管理员系统**: 独立的管理系统，用于配置系统核心参数和管理 AI 模型。
    """)

with info_col2:
    st.warning("""
    **注意事项**:
    
    - 修改配置后需要重启后端服务才能生效
    - 模型更新需要验证模型文件完整性
    - 请谨慎操作，避免影响系统正常运行
    """)

