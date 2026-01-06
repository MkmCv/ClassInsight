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
if 'refresh_token' not in st.session_state:
    st.session_state['refresh_token'] = None
if 'show_forgot_password' not in st.session_state:
    st.session_state['show_forgot_password'] = False
if 'reset_step' not in st.session_state:
    st.session_state['reset_step'] = 1  # 1=输入邮箱, 2=输入验证码
if 'reset_email' not in st.session_state:
    st.session_state['reset_email'] = ""
if 'login_attempt_info' not in st.session_state:
    st.session_state['login_attempt_info'] = None


def get_login_attempt_info(username: str):
    """获取登录尝试信息"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/login/attempt-info",
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


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


def mock_login(username: str, password: str):
    """使用Mock数据登录（开发用）"""
    if username == "teacher001" and password:
        return True, {"user": MOCK_USER, "access_token": "mock_token"}
    return False, "账号或密码错误"


def send_verification_code(email: str):
    """发送验证码"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/forgot-password",
            json={"email": email},
            timeout=10
        )
        if response.status_code == 200:
            return True, response.json().get("message", "验证码已发送")
        else:
            try:
                error_msg = response.json().get("detail", "发送失败")
            except:
                error_msg = f"发送失败 (HTTP {response.status_code})"
            return False, error_msg
    except requests.exceptions.ConnectionError:
        return False, "无法连接到服务器"
    except Exception as e:
        return False, str(e)


def reset_password(email: str, code: str, new_password: str):
    """重置密码"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/reset-password",
            json={"email": email, "code": code, "new_password": new_password},
            timeout=10
        )
        if response.status_code == 200:
            return True, response.json().get("message", "密码重置成功")
        else:
            try:
                error_msg = response.json().get("detail", "重置失败")
            except:
                error_msg = f"重置失败 (HTTP {response.status_code})"
            return False, error_msg
    except requests.exceptions.ConnectionError:
        return False, "无法连接到服务器"
    except Exception as e:
        return False, str(e)


# ==================== 登录页面 ====================
def login():
    # 隐藏侧边栏
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center;'>🎓 ClassInsight AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280;'>基于 VHEAT 算法的新一代课堂行为智能分析系统</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 判断显示登录还是忘记密码
        if not st.session_state['show_forgot_password']:
            # ==================== 登录表单 ====================
            c1, c2 = st.columns([1.2, 1])
            with c1:
                st.image("https://img.freepik.com/free-vector/data-extraction-concept-illustration_114360-4876.jpg")
            with c2:
                st.markdown("### 欢迎回来")
                st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                
                # 账号输入
                username = st.text_input("账号", placeholder="teacher001", key="login_username")
                
                # 密码输入
                password = st.text_input("密码", type="password", placeholder="••••••", key="login_password")
                
                # 获取登录尝试信息
                if username and USE_BACKEND_API:
                    attempt_info = get_login_attempt_info(username)
                    if attempt_info:
                        st.session_state['login_attempt_info'] = attempt_info
                        if attempt_info.get('failed_count', 0) > 0:
                            remaining = attempt_info.get('remaining_attempts', 5)
                            if remaining > 0:
                                st.warning(f"⚠️ 剩余登录尝试次数：{remaining}")
                            else:
                                locked_until = attempt_info.get('locked_until')
                                if locked_until:
                                    st.error("🔒 账户已被锁定，请稍后再试")
                
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                
                # 登录按钮
                if st.button("登 录", type="primary", use_container_width=True):
                    if not username or not password:
                        st.error("请输入账号和密码")
                    else:
                        with st.spinner("正在验证身份..."):
                            if USE_BACKEND_API:
                                success, result = api_login(username, password)
                            else:
                                success, result = mock_login(username, password)
                            
                            if success:
                                st.session_state['authentication_status'] = True
                                st.session_state['user'] = result.get('user', {})
                                st.session_state['access_token'] = result.get('access_token')
                                st.session_state['refresh_token'] = result.get('refresh_token')
                                st.session_state['login_attempt_info'] = None
                                
                                st.success("✅ 登录成功！正在跳转...")
                                time.sleep(0.5)
                                st.switch_page("pages/1_🏠_首页.py")
                            else:
                                st.error(result)
                
                # 忘记密码链接
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.caption("还没有账号？请联系管理员")
                if st.button("🔑 忘记密码", use_container_width=True):
                    st.session_state['show_forgot_password'] = True
                    st.session_state['reset_step'] = 1
                    st.rerun()
        
        else:
            # ==================== 忘记密码表单 ====================
            st.markdown("### 🔑 找回密码")
            
            if st.session_state['reset_step'] == 1:
                # 步骤1：输入邮箱
                st.info("请输入您注册时使用的邮箱，我们将发送验证码。")
                
                email = st.text_input("注册邮箱", placeholder="your@email.com", key="reset_email_input")
                
                col_send, col_back = st.columns([2, 1])
                
                with col_send:
                    if st.button("📧 发送验证码", type="primary", use_container_width=True):
                        if not email or "@" not in email:
                            st.error("请输入有效的邮箱地址")
                        else:
                            with st.spinner("正在发送验证码..."):
                                success, message = send_verification_code(email)
                                if success:
                                    st.success(message)
                                    st.session_state['reset_email'] = email
                                    st.session_state['reset_step'] = 2
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(message)
                
                with col_back:
                    if st.button("← 返回登录", use_container_width=True):
                        st.session_state['show_forgot_password'] = False
                        st.session_state['reset_step'] = 1
                        st.rerun()
            
            elif st.session_state['reset_step'] == 2:
                # 步骤2：输入验证码和新密码
                st.success(f"验证码已发送至 **{st.session_state['reset_email']}**")
                st.caption("⏰ 验证码10分钟内有效")
                
                code = st.text_input("验证码", placeholder="6位数字", max_chars=6, key="reset_code")
                new_password = st.text_input("新密码", type="password", placeholder="至少8位", key="reset_new_pwd")
                confirm_password = st.text_input("确认密码", type="password", placeholder="再次输入新密码", key="reset_confirm_pwd")
                
                col_reset, col_resend, col_back = st.columns([2, 1, 1])
                
                with col_reset:
                    if st.button("✅ 重置密码", type="primary", use_container_width=True):
                        if not code or len(code) != 6:
                            st.error("请输入6位验证码")
                        elif not new_password or len(new_password) < 8:
                            st.error("密码至少8位")
                        elif new_password != confirm_password:
                            st.error("两次密码不一致")
                        else:
                            with st.spinner("正在重置密码..."):
                                success, message = reset_password(
                                    st.session_state['reset_email'],
                                    code,
                                    new_password
                                )
                                if success:
                                    st.success(message)
                                    st.balloons()
                                    st.session_state['show_forgot_password'] = False
                                    st.session_state['reset_step'] = 1
                                    st.session_state['reset_email'] = ""
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(message)
                
                with col_resend:
                    if st.button("🔄 重发", use_container_width=True):
                        with st.spinner("发送中..."):
                            success, message = send_verification_code(st.session_state['reset_email'])
                            if success:
                                st.success("已重新发送")
                            else:
                                st.error(message)
                
                with col_back:
                    if st.button("← 返回", use_container_width=True):
                        st.session_state['show_forgot_password'] = False
                        st.session_state['reset_step'] = 1
                        st.rerun()


# ==================== 路由控制 ====================
if not st.session_state['authentication_status']:
    login()
else:
    st.switch_page("pages/1_🏠_首页.py")