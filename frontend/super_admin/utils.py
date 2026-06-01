"""
超级管理员系统工具函数
"""
import os
import streamlit as st
from pathlib import Path
import json
from datetime import datetime, timedelta

def load_css(file_name="style.css"):
    """加载自定义 CSS 文件"""
    # 从 frontend 目录加载 CSS
    current_file = os.path.abspath(__file__)
    super_admin_dir = os.path.dirname(current_file)
    system_dir = os.path.dirname(super_admin_dir)
    frontend_dir = os.path.join(system_dir, "frontend")
    
    css_path = os.path.join(frontend_dir, file_name)
    
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # 如果找不到 CSS，使用默认样式
        pass
    except Exception as e:
        # 静默失败，不影响功能
        pass


def render_sidebar():
    """渲染超级管理员侧边栏"""
    with st.sidebar:
        user = st.session_state.get('super_admin_user', {})
        username = user.get('username', '超级管理员')
        
        st.markdown(f"""
        <div style="padding: 1rem; background: linear-gradient(135deg, #DC2626 0%, #991B1B 100%); 
                    border-radius: 10px; color: white; margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; font-weight: 600;">🔐 {username}</div>
            <div style="font-size: 0.85rem; opacity: 0.9;">超级管理员</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 导航菜单
        st.markdown("### 📋 导航")
        
        if st.button("🏠 超级管理员中心", use_container_width=True, type="primary", key="nav_center"):
            st.switch_page("pages/0_🏠_超级管理员中心.py")
        
        if st.button("🔒 登录安全配置", use_container_width=True, type="primary", key="nav_security"):
            st.switch_page("pages/1_🔒_登录安全配置.py")
        
        if st.button("🤖 模型管理", use_container_width=True, type="primary", key="nav_model"):
            st.switch_page("pages/2_🤖_模型管理.py")
        
        st.markdown("---")
        
        # 退出登录
        if st.button("🚪 退出登录", use_container_width=True, type="secondary", key="nav_logout"):
            # 清除认证文件
            clear_super_admin_auth()
            
            st.session_state['super_admin_auth'] = False
            st.session_state['super_admin_user'] = None
            st.session_state['super_admin_token'] = None
            st.session_state['super_admin_loaded'] = False
            st.success("已退出登录，正在跳转...")
            st.switch_page("app.py")


def get_api_headers():
    """获取带认证的请求头"""
    headers = {"Content-Type": "application/json"}
    if 'super_admin_token' in st.session_state and st.session_state['super_admin_token']:
        headers["Authorization"] = f"Bearer {st.session_state['super_admin_token']}"
    return headers


# ==================== 登录持久化功能 ====================

def get_super_admin_session_file():
    """获取超级管理员 session 文件路径"""
    temp_dir = Path("./temp_sessions")
    temp_dir.mkdir(exist_ok=True)
    return temp_dir / "super_admin_session.json"


def save_super_admin_auth():
    """保存超级管理员认证信息到文件"""
    try:
        session_file = get_super_admin_session_file()
        auth_data = {
            'user': st.session_state.get('super_admin_user'),
            'access_token': st.session_state.get('super_admin_token'),
            'timestamp': datetime.now().isoformat()
        }
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f)
    except Exception as e:
        pass  # 静默失败


def load_super_admin_auth():
    """从文件加载超级管理员认证信息"""
    try:
        session_file = get_super_admin_session_file()
        
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            # 检查是否过期（24小时）
            timestamp = datetime.fromisoformat(auth_data.get('timestamp', ''))
            if datetime.now() - timestamp < timedelta(hours=24):
                st.session_state['super_admin_user'] = auth_data.get('user')
                st.session_state['super_admin_token'] = auth_data.get('access_token')
                st.session_state['super_admin_auth'] = True
                return True
            else:
                # 过期，删除文件
                session_file.unlink()
        return False
    except Exception as e:
        return False


def clear_super_admin_auth():
    """清除超级管理员认证文件"""
    try:
        session_file = get_super_admin_session_file()
        if session_file.exists():
            session_file.unlink()
    except:
        pass


def check_super_admin_auth():
    """检查超级管理员是否已登录，如果未登录则跳转到登录页"""
    # 只在第一次检查时尝试从文件恢复
    if 'super_admin_loaded' not in st.session_state:
        st.session_state['super_admin_loaded'] = load_super_admin_auth()
    
    # 检查是否已登录
    if not st.session_state.get('super_admin_auth', False):
        st.switch_page("app.py")
    
    # 更新文件（刷新时间戳）
    if st.session_state.get('super_admin_auth'):
        save_super_admin_auth()
    
    return True

