import streamlit as st
import time
from mock_data import MOCK_USER
from utils import load_css

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
                    with st.spinner("正在验证身份..."):
                        time.sleep(0.5)
                        if username == "teacher001" and password:
                            st.session_state['authentication_status'] = True
                            st.session_state['user'] = MOCK_USER
                            st.switch_page("pages/1_🏠_首页.py")
                        else:
                            st.error("账号或密码错误")

# ==================== 路由控制 ====================
if not st.session_state['authentication_status']:
    login()
else:
    # 已登录则直接跳转首页
    st.switch_page("pages/1_🏠_首页.py")
