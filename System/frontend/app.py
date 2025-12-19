import streamlit as st
import time
import os
import requests
from mock_data import MOCK_USER
from utils import load_css

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# 是否使用后端API（False则使用mock数据）
USE_BACKEND_API = True

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="ClassInsight AI - 登录",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_css()

# 初始化Session
if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None


def api_login(username: str, password: str):
    """调用后端登录API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login/json",
            json={"username": username, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            # 安全地解析错误响应
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


def mock_login(username: str, password: str):
    """使用Mock数据登录（开发用）"""
    if username == "teacher001" and password:
        return True, {"user": MOCK_USER, "access_token": "mock_token"}
    return False, "账号或密码错误"


# ==================== 登录逻辑 ====================
def login():
    # 隐藏侧边栏的 CSS
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        section[data-testid="stSidebar"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("<h1 style='text-align: center;'>ClassInsight AI</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #6B7280;'>基于 VHEAT 算法的新一代课堂行为智能分析系统</p>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1.2, 1])
            with c1:
                st.image("https://img.freepik.com/free-vector/data-extraction-concept-illustration_114360-4876.jpg", use_column_width=True)
            with c2:
                st.markdown("### 欢迎回来")
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                username = st.text_input("账号", placeholder="teacher001")
                password = st.text_input("密码", type="password", placeholder="••••••")
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                if st.button("登 录", type="primary", use_container_width=True):
                    if not username or not password:
                        st.error("请输入账号和密码")
                    else:
                        with st.spinner("正在验证身份..."):
                            # 根据配置选择登录方式
                            if USE_BACKEND_API:
                                success, result = api_login(username, password)
                            else:
                                success, result = mock_login(username, password)
                            
                            if success:
                                st.session_state['authentication_status'] = True
                                st.session_state['user'] = result.get('user', {})
                                st.session_state['access_token'] = result.get('access_token')
                                st.success("登录成功！正在跳转...")
                                time.sleep(0.5)
                                st.switch_page("pages/1_🏠_首页.py")
                            else:
                                st.error(result)
                
                # 注册提示
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.caption("还没有账号？请联系管理员注册")

# ==================== 路由控制 ====================
if not st.session_state['authentication_status']:
    login()
else:
    # 已登录则直接跳转首页
    st.switch_page("pages/1_🏠_首页.py")
