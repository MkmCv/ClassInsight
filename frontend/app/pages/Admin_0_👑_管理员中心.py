import streamlit as st
import requests
import sys
import os
from datetime import datetime

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, get_api_headers, check_authentication

st.set_page_config(page_title="管理员中心 - ClassInsight", page_icon="👑", layout="wide")

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
@st.cache_data(ttl=60, show_spinner=False)
def get_system_stats(_headers_tuple):
    """获取系统统计信息"""
    try:
        headers = dict(_headers_tuple)
        
        # 获取用户统计
        users_response = requests.get(
            f"{API_BASE_URL}/admin/users",
            headers=headers,
            params={"page": 1, "page_size": 1000},  # 获取所有用户以统计总数
            timeout=5
        )
        total_users = 0
        if users_response.status_code == 200:
            users_data = users_response.json()
            # API 返回的是列表
            if isinstance(users_data, list):
                total_users = len(users_data)
            elif isinstance(users_data, dict):
                # 如果是分页响应，尝试获取 total
                total_users = users_data.get("total", len(users_data.get("items", [])))
        
        # 获取视频统计
        videos_response = requests.get(
            f"{API_BASE_URL}/videos",
            headers=headers,
            params={"page": 1, "page_size": 1000},  # 获取所有视频以统计总数
            timeout=5
        )
        total_videos = 0
        if videos_response.status_code == 200:
            videos_data = videos_response.json()
            # 检查返回的是字典还是列表
            if isinstance(videos_data, dict):
                # 分页响应
                total_videos = videos_data.get("total", len(videos_data.get("items", [])))
            elif isinstance(videos_data, list):
                total_videos = len(videos_data)
        
        # 获取登录安全配置
        config_response = requests.get(
            f"{API_BASE_URL}/admin/login-security-config",
            headers=headers,
            timeout=5
        )
        security_config = {}
        if config_response.status_code == 200:
            security_config = config_response.json()
        
        # 获取活跃用户数（最近7天有登录的用户）
        # 这里简化处理，实际可以从登录历史统计
        active_users = total_users  # 占位符
        
        return {
            "total_users": total_users,
            "total_videos": total_videos,
            "active_users": active_users,
            "security_config": security_config
        }
    except Exception as e:
        # 不在缓存函数中显示错误（会导致重复显示）
        # st.error(f"获取系统统计失败: {str(e)}")
        return {
            "total_users": 0,
            "total_videos": 0,
            "active_users": 0,
            "security_config": {},
            "error": str(e)
        }

# ==================== 页面内容 ====================
st.title("👑 管理员中心")

headers_tuple = tuple(get_api_headers().items())
stats = get_system_stats(headers_tuple)

# 显示错误信息（如果有）
if stats.get("error"):
    st.error(f"⚠️ 获取系统统计失败: {stats.get('error')}")
    st.info("💡 提示：请检查后端服务是否正常运行，或稍后重试")

# 系统概览卡片
st.subheader("📊 系统概览")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("总用户数", stats["total_users"])

with col2:
    st.metric("总视频数", stats["total_videos"])

with col3:
    st.metric("活跃用户", stats["active_users"])

with col4:
    security_config = stats.get("security_config", {})
    max_attempts = security_config.get("max_login_attempts", 5)
    st.metric("最大登录失败次数", max_attempts)

st.divider()

# 快速操作
st.subheader("🚀 快速操作")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("👤 用户管理", use_container_width=True, type="primary", key="quick_user_mgmt"):
        st.switch_page("pages/5_👤_用户管理.py")

with col2:
    if st.button("📅 课表管理", use_container_width=True, type="primary", key="quick_schedule_mgmt"):
        st.switch_page("pages/6_📅_课表管理.py")

with col3:
    if st.button("📊 登录失败摘要", use_container_width=True, key="quick_security_summary"):
        st.switch_page("pages/Admin_1_📊_登录失败摘要.py")

st.divider()

# 系统配置
st.subheader("⚙️ 系统配置")

security_config = stats.get("security_config", {})
if security_config:
    st.markdown("### 登录安全配置")
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        st.info(f"**最大登录失败次数**: {security_config.get('max_login_attempts', 5)}")
    
    with config_col2:
        st.info(f"**账户锁定时间**: {security_config.get('lockout_minutes', 15)} 分钟")
    
    with config_col3:
        st.info(f"**需要验证码的失败次数**: {security_config.get('captcha_required_after', 3)}")
    
    st.caption("💡 提示：系统配置修改需要编辑后端配置文件 `backend/app/core/config.py` 并重启服务")
else:
    st.warning("无法获取系统配置信息")

st.divider()

# 功能导航
st.subheader("📋 管理员功能")

admin_features = [
    {
        "title": "👤 用户管理",
        "description": "管理系统用户（教师/管理员），注册新账号或维护现有信息",
        "page": "pages/5_👤_用户管理.py"
    },
    {
        "title": "📅 课表管理",
        "description": "管理课程表，添加、编辑或删除课程安排",
        "page": "pages/6_📅_课表管理.py"
    },
    {
        "title": "📊 登录失败摘要",
        "description": "查看登录失败记录摘要和统计信息",
        "page": "pages/Admin_1_📊_登录失败摘要.py"
    }
]

for idx, feature in enumerate(admin_features):
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {feature['title']}")
            st.caption(feature['description'])
        with col2:
            # 使用索引确保 key 唯一
            if st.button("前往", key=f"goto_feature_{idx}_{feature['title']}", use_container_width=True):
                st.switch_page(feature['page'])
        st.divider()
