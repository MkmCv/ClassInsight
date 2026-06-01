import os
import streamlit as st
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

def load_css(file_name="style.css"):
    """
    加载自定义 CSS 文件。
    
    Args:
        file_name (str): CSS 文件名，默认为 'style.css'。
                         函数会自动从 frontend 根目录查找该文件。
    """
    # 获取当前脚本的绝对路径
    current_file = os.path.abspath(__file__)
    # 获取 frontend 目录路径 (当前 utils.py 就在 frontend 目录下)
    frontend_dir = os.path.dirname(current_file)
    
    file_path = os.path.join(frontend_dir, file_name)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        
        # 如果不是管理员，添加额外的隐藏逻辑（全局应用）
        # 安全获取用户信息（处理 None 的情况）
        user = st.session_state.get('user') or {}
        role = user.get('role', 'teacher') if isinstance(user, dict) else 'teacher'
        
        if role != 'admin':
            # 添加全局隐藏 CSS
            additional_css = """
            /* 全局隐藏管理员页面链接（非管理员用户） */
            div[data-testid="stSidebarNav"] a[href*="Admin_"],
            div[data-testid="stSidebarNav"] a[href*="5_"],
            div[data-testid="stSidebarNav"] a[href*="6_"],
            div[data-testid="stSidebarNav"] a[href*="%E7%94%A8%E6%88%B7%E7%AE%A1%E7%90%86"],
            div[data-testid="stSidebarNav"] a[href*="%E8%AF%BE%E8%A1%A8%E7%AE%A1%E7%90%86"],
            div[data-testid="stSidebarNav"] a[href*="用户管理"],
            div[data-testid="stSidebarNav"] a[href*="课表管理"] {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                height: 0 !important;
                width: 0 !important;
                pointer-events: none !important;
            }
            div[data-testid="stSidebarNav"] ul li:has(a[href*="Admin_"]),
            div[data-testid="stSidebarNav"] ul li:has(a[href*="5_"]),
            div[data-testid="stSidebarNav"] ul li:has(a[href*="6_"]),
            div[data-testid="stSidebarNav"] ul li:has(a[href*="%E7%94%A8%E6%88%B7%E7%AE%A1%E7%90%86"]),
            div[data-testid="stSidebarNav"] ul li:has(a[href*="%E8%AF%BE%E8%A1%A8%E7%AE%A1%E7%90%86"]),
            div[data-testid="stSidebarNav"] ul li:has(a[href*="用户管理"]),
            div[data-testid="stSidebarNav"] ul li:has(a[href*="课表管理"]) {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            """
            css_content += additional_css
        
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS 文件未找到: {file_path}")
    except UnicodeDecodeError:
        st.error(f"CSS 文件编码错误，请确保使用 UTF-8 编码: {file_path}")
    except Exception as e:
        st.error(f"加载 CSS 时发生未知错误: {str(e)}")


def render_sidebar():
    """
    渲染通用侧边栏：用户信息 + 导航菜单 + 退出登录按钮
    同时隐藏 Streamlit 自动生成的管理员页面链接（非管理员用户）
    """
    # 安全获取用户信息（处理 None 的情况）
    user = st.session_state.get('user') or {}
    username = user.get('username', '用户') if isinstance(user, dict) else '用户'
    role = user.get('role', 'teacher') if isinstance(user, dict) else 'teacher'
    role_display = "👑 管理员" if role == 'admin' else "👨‍🏫 教师"
    
    # 如果不是管理员，强制隐藏管理员页面链接
    if role != 'admin':
        st.markdown("""
        <style>
        /* 强制隐藏管理员页面链接（非管理员用户）- 多重选择器 */
        /* 方法1: 通过 href 属性（包括 URL 编码） */
        div[data-testid="stSidebarNav"] a[href*="Admin_0"],
        div[data-testid="stSidebarNav"] a[href*="Admin_1"],
        div[data-testid="stSidebarNav"] a[href*="Admin_"],
        div[data-testid="stSidebarNav"] a[href*="5_"],
        div[data-testid="stSidebarNav"] a[href*="6_"],
        div[data-testid="stSidebarNav"] a[href*="%E7%94%A8%E6%88%B7%E7%AE%A1%E7%90%86"],
        div[data-testid="stSidebarNav"] a[href*="%E8%AF%BE%E8%A1%A8%E7%AE%A1%E7%90%86"],
        div[data-testid="stSidebarNav"] a[href*="用户管理"],
        div[data-testid="stSidebarNav"] a[href*="课表管理"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            pointer-events: none !important;
            position: absolute !important;
            left: -9999px !important;
        }
        /* 隐藏包含管理员页面的列表项 */
        div[data-testid="stSidebarNav"] ul li:has(a[href*="Admin_0"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="Admin_1"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="Admin_"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="5_"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="6_"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="%E7%94%A8%E6%88%B7%E7%AE%A1%E7%90%86"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="%E8%AF%BE%E8%A1%A8%E7%AE%A1%E7%90%86"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="用户管理"]),
        div[data-testid="stSidebarNav"] ul li:has(a[href*="课表管理"]) {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        </style>
        <script>
        // 使用 JavaScript 强制隐藏管理员页面（多重保护）
        (function() {
            function hideAdminPages() {
                // 方法1: 通过 data-testid 选择器
                const nav = document.querySelector('[data-testid="stSidebarNav"]');
                if (nav) {
                    // 查找所有链接
                    const links = nav.querySelectorAll('a');
                    links.forEach(link => {
                        const href = link.getAttribute('href') || '';
                        const text = (link.textContent || link.innerText || '').trim();
                        
                        // 检查是否是管理员页面（通过 href 或文本）
                        // 检查文件名模式：5_ 或 6_ 开头的文件（用户管理和课表管理）
                        const isAdminPage = 
                            href.includes('Admin_0') || 
                            href.includes('Admin_1') ||
                            href.includes('Admin_') ||
                            /5_[^/]*/.test(href) ||  // 匹配 5_ 开头的文件名
                            /6_[^/]*/.test(href) ||  // 匹配 6_ 开头的文件名
                            href.includes('5_') || 
                            href.includes('6_') ||
                            href.includes('%E7%94%A8%E6%88%B7%E7%AE%A1%E7%90%86') ||  // URL 编码的"用户管理"
                            href.includes('%E8%AF%BE%E8%A1%A8%E7%AE%A1%E7%90%86') ||  // URL 编码的"课表管理"
                            href.includes('用户管理') ||
                            href.includes('课表管理') ||
                            text.includes('管理员中心') ||
                            text.includes('用户管理') ||
                            text.includes('课表管理') ||
                            text.includes('登录失败摘要');
                        
                        if (isAdminPage) {
                            // 多重隐藏
                            link.style.display = 'none';
                            link.style.visibility = 'hidden';
                            link.style.opacity = '0';
                            link.style.height = '0';
                            link.style.width = '0';
                            link.style.padding = '0';
                            link.style.margin = '0';
                            link.style.pointerEvents = 'none';
                            link.style.position = 'absolute';
                            link.style.left = '-9999px';
                            
                            // 隐藏父元素
                            const li = link.closest('li');
                            if (li) {
                                li.style.display = 'none';
                                li.style.visibility = 'hidden';
                                li.style.height = '0';
                                li.style.margin = '0';
                                li.style.padding = '0';
                            }
                            
                            // 隐藏父元素的父元素（如果整个 ul 只有一个 li）
                            const ul = link.closest('ul');
                            if (ul) {
                                const visibleLis = Array.from(ul.querySelectorAll('li')).filter(
                                    li => li.style.display !== 'none'
                                );
                                if (visibleLis.length === 0) {
                                    const parentLi = ul.closest('li');
                                    if (parentLi) {
                                        parentLi.style.display = 'none';
                                    }
                                }
                            }
                        }
                    });
                }
                
                // 方法2: 通过类名或属性选择器（备用）
                const allAdminLinks = document.querySelectorAll(
                    'a[href*="Admin_"], a[href*="5_"], a[href*="6_"]'
                );
                allAdminLinks.forEach(link => {
                    const href = link.getAttribute('href') || '';
                    const text = (link.textContent || link.innerText || '').trim();
                    // 只隐藏确实是管理员页面的链接（避免误隐藏其他 5_ 或 6_ 开头的文件）
                    if (href.includes('Admin_') || 
                        (href.includes('5_') && (text.includes('用户管理') || href.includes('用户管理'))) ||
                        (href.includes('6_') && (text.includes('课表管理') || href.includes('课表管理')))) {
                        link.style.display = 'none';
                        link.style.visibility = 'hidden';
                        link.style.pointerEvents = 'none';
                        const li = link.closest('li');
                        if (li) li.style.display = 'none';
                    }
                });
            }
            
            // 立即执行多次，确保捕获所有情况
            hideAdminPages();
            setTimeout(hideAdminPages, 50);
            setTimeout(hideAdminPages, 100);
            setTimeout(hideAdminPages, 300);
            setTimeout(hideAdminPages, 500);
            setTimeout(hideAdminPages, 1000);
            
            // 监听 DOM 变化（Streamlit 可能动态加载）
            const observer = new MutationObserver(function(mutations) {
                hideAdminPages();
            });
            observer.observe(document.body, { 
                childList: true, 
                subtree: true,
                attributes: true,
                attributeFilter: ['href', 'class', 'style']
            });
            
            // 监听页面事件
            window.addEventListener('load', hideAdminPages);
            document.addEventListener('DOMContentLoaded', hideAdminPages);
            document.addEventListener('visibilitychange', function() {
                if (!document.hidden) {
                    hideAdminPages();
                }
            });
            
            // 定期检查（防止动态加载）
            setInterval(hideAdminPages, 2000);
        })();
        </script>
        """, unsafe_allow_html=True)
    
    with st.sidebar:
        # 用户信息
        st.markdown(f"""
        <div style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; color: white; margin-bottom: 1rem;">
            <div style="font-size: 1.2rem; font-weight: 600;">👤 {username}</div>
            <div style="font-size: 0.85rem; opacity: 0.9;">{role_display}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 导航菜单
        st.markdown("### 📋 导航")
        
        # 通用页面（所有用户）
        if st.button("🏠 首页", use_container_width=True, type="secondary"):
            st.switch_page("pages/1_🏠_首页.py")
        
        if st.button("📤 视频上传", use_container_width=True, type="secondary"):
            st.switch_page("pages/2_📤_视频上传.py")
        
        if st.button("📈 行为分析", use_container_width=True, type="secondary"):
            st.switch_page("pages/3_📈_行为分析.py")
        
        if st.button("💡 教学建议", use_container_width=True, type="secondary"):
            st.switch_page("pages/4_💡_教学建议.py")
        
        # 管理员专用页面（仅管理员可见）
        if role == 'admin':
            st.markdown("---")
            st.markdown("### 👑 管理员")
            
            if st.button("👑 管理员中心", use_container_width=True, type="primary"):
                st.switch_page("pages/Admin_0_👑_管理员中心.py")
            
            if st.button("👤 用户管理", use_container_width=True, type="primary", key="sidebar_user_mgmt"):
                st.switch_page("pages/5_👤_用户管理.py")
            
            if st.button("📅 课表管理", use_container_width=True, type="primary", key="sidebar_schedule_mgmt"):
                st.switch_page("pages/6_📅_课表管理.py")
            
            if st.button("📊 登录失败摘要", use_container_width=True, type="primary", key="sidebar_security_summary"):
                st.switch_page("pages/Admin_1_📊_登录失败摘要.py")
        
        st.markdown("---")
        
        # 退出登录按钮
        if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
            # 清除认证文件
            clear_auth_file()
            
            # 清除所有session状态
            st.session_state['authentication_status'] = False
            st.session_state['user'] = None
            st.session_state['access_token'] = None
            st.session_state['auth_loaded_from_file'] = False
            # 清除其他可能的缓存
            for key in list(st.session_state.keys()):
                if key not in ['authentication_status', 'user', 'access_token', 'auth_loaded_from_file']:
                    del st.session_state[key]
            st.success("已退出登录，正在跳转...")
            st.switch_page("app.py")


def get_session_file_path():
    """获取 session 文件路径"""
    # 使用临时目录存储 session
    temp_dir = Path("./temp_sessions")
    temp_dir.mkdir(exist_ok=True)
    
    # 使用固定的文件名（单用户模式，适合教学演示系统）
    # Streamlit 的 session ID 在刷新时会变化，所以不能依赖它
    session_file = temp_dir / "last_login.json"
    return session_file


def save_auth_to_file():
    """保存认证信息到文件"""
    try:
        session_file = get_session_file_path()
        auth_data = {
            'user': st.session_state.get('user'),
            'access_token': st.session_state.get('access_token'),
            'refresh_token': st.session_state.get('refresh_token'),
            'timestamp': datetime.now().isoformat()
        }
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(auth_data, f)
    except Exception as e:
        pass  # 静默失败


def load_auth_from_file():
    """从文件加载认证信息"""
    try:
        session_file = get_session_file_path()
        
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            # 检查是否过期（24小时）
            timestamp = datetime.fromisoformat(auth_data.get('timestamp', ''))
            if datetime.now() - timestamp < timedelta(hours=24):
                st.session_state['user'] = auth_data.get('user')
                st.session_state['access_token'] = auth_data.get('access_token')
                st.session_state['refresh_token'] = auth_data.get('refresh_token')
                st.session_state['authentication_status'] = True
                return True
            else:
                # 过期，删除文件
                session_file.unlink()
        return False
    except Exception as e:
        return False


def clear_auth_file():
    """清除认证文件"""
    try:
        session_file = get_session_file_path()
        if session_file.exists():
            session_file.unlink()
    except:
        pass


def check_authentication():
    """检查用户是否已登录，如果未登录则跳转到登录页"""
    # 只在第一次检查时尝试从文件恢复
    if 'auth_loaded_from_file' not in st.session_state:
        st.session_state['auth_loaded_from_file'] = load_auth_from_file()
    
    # 检查是否已登录
    if not st.session_state.get('authentication_status', False):
        st.switch_page("app.py")
    
    # 更新文件（刷新时间戳）
    if st.session_state.get('authentication_status'):
        save_auth_to_file()
    
    return True


def get_api_headers():
    """获取带认证的请求头"""
    headers = {"Content-Type": "application/json"}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers






