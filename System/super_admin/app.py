"""
超级管理员系统 - 登录页面
"""
import streamlit as st
import os
import requests
import sys

# 添加父目录到路径，以便导入共享的 CSS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frontend.utils import load_css
from utils import save_super_admin_auth

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="超级管理员 - ClassInsight",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_css()

# 初始化 Session
if 'super_admin_auth' not in st.session_state:
    st.session_state['super_admin_auth'] = False
if 'super_admin_user' not in st.session_state:
    st.session_state['super_admin_user'] = None
if 'super_admin_token' not in st.session_state:
    st.session_state['super_admin_token'] = None


def api_login(username: str, password: str):
    """调用后端登录API"""
    try:
        payload = {"username": username, "password": password}
        
        response = requests.post(
            f"{API_BASE_URL}/auth/login/json",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # 检查是否为超级管理员
            user = data.get("user", {})
            if user.get("role") != "super_admin":
                return False, "此账号不是超级管理员"
            return True, data
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", "登录失败")
            except:
                error_msg = f"登录失败 (HTTP {response.status_code})"
            return False, error_msg
            
    except requests.exceptions.ConnectionError:
        return False, "无法连接到服务器，请确认后端服务已启动"
    except requests.exceptions.Timeout:
        return False, "请求超时，请稍后重试"
    except Exception as e:
        return False, f"请求错误: {str(e)}"


# ==================== 页面内容 ====================
st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="background: linear-gradient(90deg, #4F46E5 0%, #EC4899 100%);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   font-size: 3rem;
                   margin-bottom: 0.5rem;">🔐 超级管理员</h1>
        <p style="color: #6B7280; font-size: 1.1rem;">ClassInsight 系统管理</p>
    </div>
""", unsafe_allow_html=True)

# 如果已登录，跳转到主页
if st.session_state.get('super_admin_auth'):
    st.switch_page("pages/0_🏠_超级管理员中心.py")

# 登录表单
with st.form("super_admin_login", clear_on_submit=False):
    st.markdown("### 登录")
    
    username = st.text_input("用户名", placeholder="请输入超级管理员用户名", key="super_admin_username")
    password = st.text_input("密码", type="password", placeholder="请输入密码", key="super_admin_password")
    
    submit_button = st.form_submit_button("登录", use_container_width=True, type="primary")
    
    if submit_button:
        if not username or not password:
            st.error("请输入用户名和密码")
        else:
            with st.spinner("正在登录..."):
                success, result = api_login(username, password)
                
                if success:
                    # 保存登录状态
                    st.session_state['super_admin_auth'] = True
                    st.session_state['super_admin_user'] = result.get("user")
                    st.session_state['super_admin_token'] = result.get("access_token")
                    
                    # 保存认证信息到文件（支持刷新后恢复）
                    save_super_admin_auth()
                    
                    st.success("登录成功！正在跳转...")
                    st.rerun()
                else:
                    st.error(result)

st.markdown("---")
st.caption("💡 提示：只有超级管理员账号可以登录此系统")

