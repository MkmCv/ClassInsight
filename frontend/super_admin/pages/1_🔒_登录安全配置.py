"""
登录安全配置 - 超级管理员
"""
import streamlit as st
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, get_api_headers, check_super_admin_auth

st.set_page_config(page_title="登录安全配置 - 超级管理员", page_icon="🔒", layout="wide")

load_css()

# ==================== 权限检查 ====================
check_super_admin_auth()

render_sidebar()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.title("🔒 登录安全配置")

# ==================== 数据获取函数 ====================
@st.cache_data(ttl=30, show_spinner=False)
def get_security_config(_headers_tuple):
    """获取登录安全配置"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/super-admin/login-security-config",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

def update_security_config(max_attempts, lockout_minutes, captcha_after):
    """更新登录安全配置"""
    try:
        headers = get_api_headers()
        payload = {
            "max_login_attempts": max_attempts,
            "lockout_minutes": lockout_minutes,
            "captcha_required_after": captcha_after
        }
        response = requests.put(
            f"{API_BASE_URL}/super-admin/login-security-config",
            headers=headers,
            json=payload,
            timeout=5
        )
        if response.status_code == 200:
            return True, response.json()
        return False, response.json().get("detail", "更新失败")
    except Exception as e:
        return False, str(e)

# ==================== 页面内容 ====================
headers_tuple = tuple(get_api_headers().items())
config = get_security_config(headers_tuple)

if not config:
    st.error("无法获取登录安全配置，请检查后端服务是否正常运行")
    st.stop()

# 当前配置显示
st.subheader("📋 当前配置")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "最大登录失败次数",
        config.get("max_login_attempts", 5),
        help="用户连续登录失败达到此次数后，账户将被锁定"
    )

with col2:
    st.metric(
        "账户锁定时间",
        f"{config.get('lockout_minutes', 15)} 分钟",
        help="账户被锁定后的持续时间"
    )

with col3:
    st.metric(
        "需要验证码的失败次数",
        config.get("captcha_required_after", 3),
        help="登录失败达到此次数后，需要输入验证码（当前功能已移除）"
    )

st.divider()

# 配置修改
st.subheader("⚙️ 修改配置")

st.warning("""
**重要提示**：

当前配置存储在 `backend/app/core/config.py` 文件中。修改配置需要：

1. 编辑 `backend/app/core/config.py` 文件
2. 修改以下配置项：
   - `MAX_LOGIN_ATTEMPTS` - 最大登录失败次数
   - `LOGIN_LOCKOUT_MINUTES` - 锁定时间（分钟）
   - `CAPTCHA_REQUIRED_AFTER` - 需要验证码的失败次数
3. **重启后端服务**使配置生效

**注意**：修改配置后必须重启后端服务才能生效。
""")

with st.form("update_security_config", clear_on_submit=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_max_attempts = st.number_input(
            "最大登录失败次数",
            min_value=1,
            max_value=20,
            value=config.get("max_login_attempts", 5),
            help="建议值：3-10"
        )
    
    with col2:
        new_lockout_minutes = st.number_input(
            "账户锁定时间（分钟）",
            min_value=1,
            max_value=1440,
            value=config.get("lockout_minutes", 15),
            help="建议值：5-60"
        )
    
    with col3:
        new_captcha_after = st.number_input(
            "需要验证码的失败次数",
            min_value=1,
            max_value=10,
            value=config.get("captcha_required_after", 3),
            help="当前功能已移除"
        )
    
    submitted = st.form_submit_button("更新配置", use_container_width=True, type="primary")
    
    if submitted:
        # 检查是否有变化
        if (new_max_attempts == config.get("max_login_attempts") and
            new_lockout_minutes == config.get("lockout_minutes") and
            new_captcha_after == config.get("captcha_required_after")):
            st.info("配置未发生变化")
        else:
            with st.spinner("正在更新配置..."):
                success, result = update_security_config(
                    new_max_attempts,
                    new_lockout_minutes,
                    new_captcha_after
                )
                
                if success:
                    st.success("配置更新请求已提交")
                    st.info("""
                    **下一步操作**：
                    
                    1. 编辑 `backend/app/core/config.py` 文件
                    2. 将以下配置项修改为：
                       - `MAX_LOGIN_ATTEMPTS = {new_max_attempts}`
                       - `LOGIN_LOCKOUT_MINUTES = {new_lockout_minutes}`
                       - `CAPTCHA_REQUIRED_AFTER = {new_captcha_after}`
                    3. 重启后端服务
                    """.format(
                        new_max_attempts=new_max_attempts,
                        new_lockout_minutes=new_lockout_minutes,
                        new_captcha_after=new_captcha_after
                    ))
                    # 清除缓存
                    get_security_config.clear()
                else:
                    st.error(f"更新失败: {result}")

st.divider()

# 配置说明
st.subheader("📖 配置说明")

st.markdown("""
**配置项说明**：

1. **最大登录失败次数** (`MAX_LOGIN_ATTEMPTS`)
   - 用户连续登录失败达到此次数后，账户将被自动锁定
   - 建议值：5-10次
   - 过低可能影响正常用户，过高可能降低安全性

2. **账户锁定时间** (`LOGIN_LOCKOUT_MINUTES`)
   - 账户被锁定后，需要等待此时间才能再次尝试登录
   - 建议值：15-30分钟
   - 锁定时间过短可能无法有效防止暴力破解

3. **需要验证码的失败次数** (`CAPTCHA_REQUIRED_AFTER`)
   - 登录失败达到此次数后，系统会要求用户输入验证码
   - 当前功能已移除，保留此配置项用于未来扩展
   - 建议值：3-5次

**安全建议**：
- 定期检查登录失败记录
- 根据实际使用情况调整配置
- 监控异常登录尝试
""")

