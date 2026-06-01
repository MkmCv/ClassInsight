import streamlit as st
import requests
import sys
import os
import time
import pandas as pd
from datetime import datetime

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, check_authentication
from mock_data import MOCK_USERS_LIST

st.set_page_config(page_title="用户管理 - ClassInsight", page_icon="👤", layout="wide")

# 引入 CSS
load_css()

# ==================== 权限检查 ====================
# 检查登录（自动从 localStorage 恢复）
check_authentication()

# 渲染侧边栏（用户信息 + 退出登录）
render_sidebar()

current_user = st.session_state.get('user', {})
if current_user.get('role') != 'admin':
    st.error("⚠️ 只有管理员可以访问此页面")
    st.stop()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
USE_BACKEND_API = True  # 使用后端API

def get_api_headers():
    headers = {}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers

# ==================== 数据获取函数 ====================
@st.cache_data(ttl=10, show_spinner=False)
def get_users(_headers_tuple, search=None, role=None, is_active=None):
    """获取用户列表（支持搜索和筛选，缓存10秒）"""
    if USE_BACKEND_API:
        try:
            headers = dict(_headers_tuple)
            params = {}
            if search:
                params['search'] = search
            if role:
                params['role'] = role
            if is_active is not None:
                params['is_active'] = is_active
            
            response = requests.get(
                f"{API_BASE_URL}/admin/users",
                headers=headers,
                params=params,
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    else:
        # Mock数据筛选
        result = MOCK_USERS_LIST.copy()
        if search:
            result = [u for u in result if search.lower() in u.get('username', '').lower() or search.lower() in u.get('email', '').lower()]
        if role:
            result = [u for u in result if u.get('role') == role]
        return result

def create_user(user_data):
    """创建用户（成功后清除缓存）"""
    if USE_BACKEND_API:
        try:
            # 管理员创建用户也使用注册接口
            response = requests.post(f"{API_BASE_URL}/auth/register", json=user_data, headers=get_api_headers())
            if response.status_code == 201:
                return True, "用户创建成功"
            else:
                try:
                    error_msg = response.json().get("detail", "创建失败")
                except:
                    error_msg = f"创建失败 (HTTP {response.status_code})"
                return False, error_msg
        except Exception as e:
            return False, str(e)
    else:
        # 模拟添加
        new_user = user_data.copy()
        new_user['id'] = len(MOCK_USERS_LIST) + 1
        new_user['created_at'] = datetime.now().isoformat()
        MOCK_USERS_LIST.append(new_user)
        return True, "用户创建成功 (Mock)"

def update_user(user_id, user_data):
    """更新用户信息"""
    if USE_BACKEND_API:
        try:
            response = requests.put(
                f"{API_BASE_URL}/admin/users/{user_id}",
                json=user_data,
                headers=get_api_headers(),
                timeout=5
            )
            if response.status_code == 200:
                return True, response.json().get("message", "更新成功")
            else:
                try:
                    error_msg = response.json().get("detail", "更新失败")
                except:
                    error_msg = f"更新失败 (HTTP {response.status_code})"
                return False, error_msg
        except Exception as e:
            return False, str(e)
    else:
        return True, "更新成功 (Mock)"

def delete_user(user_id):
    if USE_BACKEND_API:
        try:
            response = requests.delete(f"{API_BASE_URL}/admin/users/{user_id}", headers=get_api_headers())
            return response.status_code == 200
        except:
            return False
    else:
        # 模拟删除
        global MOCK_USERS_LIST
        idx = -1
        for i, u in enumerate(MOCK_USERS_LIST):
            if u['id'] == user_id:
                idx = i
                break
        if idx != -1:
            del MOCK_USERS_LIST[idx]
            return True
        return False

def toggle_user_status(user_id):
    """切换用户状态"""
    if USE_BACKEND_API:
        try:
            response = requests.post(
                f"{API_BASE_URL}/admin/users/{user_id}/toggle-status",
                headers=get_api_headers(),
                timeout=5
            )
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, "操作失败"
        except:
            return False, "请求失败"
    else:
        return True, {"message": "状态已切换 (Mock)", "is_active": True}

def batch_delete_users(user_ids):
    """批量删除用户"""
    if USE_BACKEND_API:
        try:
            response = requests.post(
                f"{API_BASE_URL}/admin/users/batch-delete",
                json={"user_ids": user_ids},
                headers=get_api_headers(),
                timeout=5
            )
            return response.status_code == 200, response.json().get("message", "删除成功")
        except:
            return False, "请求失败"
    else:
        return True, f"已删除 {len(user_ids)} 个用户 (Mock)"

def batch_update_users(user_ids, role=None, is_active=None):
    """批量更新用户"""
    if USE_BACKEND_API:
        try:
            data = {"user_ids": user_ids}
            if role:
                data["role"] = role
            if is_active is not None:
                data["is_active"] = is_active
            
            response = requests.post(
                f"{API_BASE_URL}/admin/users/batch-update",
                json=data,
                headers=get_api_headers(),
                timeout=5
            )
            return response.status_code == 200, response.json().get("message", "更新成功")
        except:
            return False, "请求失败"
    else:
        return True, f"已更新 {len(user_ids)} 个用户 (Mock)"

# ==================== 页面布局 ====================
st.markdown("# 👤 用户管理")
st.markdown("管理系统用户（教师/管理员），注册新账号或维护现有信息。")
st.markdown("<br>", unsafe_allow_html=True)

# 初始化session state
if 'search_keyword' not in st.session_state:
    st.session_state['search_keyword'] = ""
if 'filter_role' not in st.session_state:
    st.session_state['filter_role'] = "全部"
if 'filter_status' not in st.session_state:
    st.session_state['filter_status'] = "全部"
if 'selected_user_ids' not in st.session_state:
    st.session_state['selected_user_ids'] = []

# 顶部工具栏：搜索、筛选、新增
col_search, col_filter1, col_filter2, col_add = st.columns([2, 1.5, 1.5, 1])
with col_search:
    search_keyword = st.text_input(
        "🔍 搜索用户",
        value=st.session_state['search_keyword'],
        placeholder="输入用户名或邮箱...",
        key="search_input"
    )
    st.session_state['search_keyword'] = search_keyword

with col_filter1:
    filter_role = st.selectbox(
        "角色筛选",
        ["全部", "teacher", "admin"],
        index=0 if st.session_state['filter_role'] == "全部" else (1 if st.session_state['filter_role'] == "teacher" else 2),
        key="filter_role_select"
    )
    st.session_state['filter_role'] = filter_role

with col_filter2:
    filter_status = st.selectbox(
        "状态筛选",
        ["全部", "启用", "禁用"],
        index=0 if st.session_state['filter_status'] == "全部" else (1 if st.session_state['filter_status'] == "启用" else 2),
        key="filter_status_select"
    )
    st.session_state['filter_status'] = filter_status

with col_add:
    if st.button("➕ 新增用户", type="primary", use_container_width=True):
        st.session_state['show_create_user_form'] = True

# 弹窗形式的创建表单 (使用 expander 模拟)
if st.session_state.get('show_create_user_form', False):
    with st.expander("📝 注册新用户", expanded=True):
        with st.form("create_user_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_username = st.text_input("用户名", placeholder="例如：teacher003")
                new_email = st.text_input("电子邮箱", placeholder="teacher@example.com")
                new_password = st.text_input("密码", type="password")
            with c2:
                new_role = st.selectbox("角色", ["teacher", "admin"], index=0)
                new_unit = st.text_input("所属单位", placeholder="例如：岭南师范学院")
                new_class = st.text_input("负责班级", placeholder="例如：高一(3)班")
            
            submitted = st.form_submit_button("确认创建")
            if submitted:
                if not new_username or not new_password:
                    st.error("用户名和密码为必填项")
                else:
                    data = {
                        "username": new_username,
                        "email": new_email,
                        "password": new_password,
                        "role": new_role,
                        "unit": new_unit,
                        "class_name": new_class
                    }
                    success, msg = create_user(data)
                    if success:
                        # 清除缓存，刷新数据
                        get_users.clear()
                        st.success(msg)
                        st.session_state['show_create_user_form'] = False
                        st.rerun()
                    else:
                        st.error(f"创建失败: {msg}")

# 获取筛选参数
search = st.session_state['search_keyword'] if st.session_state['search_keyword'] else None
role = st.session_state['filter_role'] if st.session_state['filter_role'] != "全部" else None
is_active = None
if st.session_state['filter_status'] == "启用":
    is_active = True
elif st.session_state['filter_status'] == "禁用":
    is_active = False

# 用户列表展示
# 获取用户列表（使用缓存）
headers_tuple = tuple(sorted(get_api_headers().items()))
users = get_users(headers_tuple, search=search, role=role, is_active=is_active)

# 前端过滤：确保不显示超级管理员（双重保护）
if users:
    users = [u for u in users if u.get('role') != 'super_admin']
    
if users:
    # 转换为DataFrame以便展示
    df = pd.DataFrame(users)
    
    # 添加状态列（如果不存在）
    if 'is_active' not in df.columns:
        df['is_active'] = True
    
    # 状态显示格式化
    df['状态'] = df['is_active'].apply(lambda x: "✅ 启用" if x else "❌ 禁用")
    
    # 自定义列名映射
    column_config = {
        "id": st.column_config.NumberColumn("ID", width="small"),
        "username": st.column_config.TextColumn("用户名", width="medium"),
        "role": st.column_config.TextColumn("角色", width="small"),
        "状态": st.column_config.TextColumn("状态", width="small"),
        "unit": st.column_config.TextColumn("所属单位", width="medium"),
        "class_name": st.column_config.TextColumn("负责班级", width="medium"),
        "email": st.column_config.TextColumn("邮箱", width="medium"),
        "created_at": st.column_config.DatetimeColumn("创建时间", format="D MMM YYYY, h:mm a"),
    }
    
    # 筛选展示的列
    display_cols = ["id", "username", "role", "状态", "unit", "class_name", "email", "created_at"]
    # 确保列存在
    display_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(
        df[display_cols],
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )
    
    # ==================== 批量操作区域 ====================
    st.markdown("### 📦 批量操作")
    
    # 构建可操作用户列表（排除当前登录用户和超级管理员）
    other_users = [
        u for u in users 
        if u.get('id') != current_user.get('id') 
        and u.get('role') != 'super_admin'  # 排除超级管理员
    ]
    
    if other_users:
        # 批量选择
        batch_col1, batch_col2, batch_col3, batch_col4 = st.columns([2, 1.5, 1.5, 1])
        
        with batch_col1:
            # 多选用户
            user_checkboxes = {}
            for user in other_users:
                user_checkboxes[user['id']] = st.checkbox(
                    f"{user.get('username')} ({user.get('role')})",
                    value=user['id'] in st.session_state['selected_user_ids'],
                    key=f"batch_select_{user['id']}"
                )
        
        with batch_col2:
            st.markdown("**批量操作**")
            batch_action = st.selectbox(
                "选择操作",
                ["无", "批量删除", "批量设为教师", "批量设为管理员", "批量启用", "批量禁用"],
                key="batch_action_select"
            )
        
        with batch_col3:
            if batch_action != "无" and st.session_state['selected_user_ids']:
                st.markdown(f"**已选择 {len(st.session_state['selected_user_ids'])} 个用户**")
                if st.button("执行批量操作", type="primary", use_container_width=True):
                    selected_ids = [uid for uid, checked in user_checkboxes.items() if checked]
                    if not selected_ids:
                        st.warning("请先选择用户")
                    else:
                        if batch_action == "批量删除":
                            st.session_state['confirm_batch_delete'] = selected_ids
                        elif batch_action == "批量设为教师":
                            success, msg = batch_update_users(selected_ids, role="teacher")
                            if success:
                                # 清除缓存，刷新数据
                                get_users.clear()
                                st.success(msg)
                                st.session_state['selected_user_ids'] = []
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        elif batch_action == "批量设为管理员":
                            success, msg = batch_update_users(selected_ids, role="admin")
                            if success:
                                # 清除缓存，刷新数据
                                get_users.clear()
                                st.success(msg)
                                st.session_state['selected_user_ids'] = []
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        elif batch_action == "批量启用":
                            success, msg = batch_update_users(selected_ids, is_active=True)
                            if success:
                                # 清除缓存，刷新数据
                                get_users.clear()
                                st.success(msg)
                                st.session_state['selected_user_ids'] = []
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                        elif batch_action == "批量禁用":
                            success, msg = batch_update_users(selected_ids, is_active=False)
                            if success:
                                # 清除缓存，刷新数据
                                get_users.clear()
                                st.success(msg)
                                st.session_state['selected_user_ids'] = []
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
        
        with batch_col4:
            if st.button("清空选择", use_container_width=True):
                st.session_state['selected_user_ids'] = []
                st.rerun()
        
        # 更新选中的用户ID
        selected_ids = [uid for uid, checked in user_checkboxes.items() if checked]
        st.session_state['selected_user_ids'] = selected_ids
        
        # 批量删除确认
        if st.session_state.get('confirm_batch_delete'):
            st.warning(f"⚠️ 确定要删除 **{len(st.session_state['confirm_batch_delete'])}** 个用户吗？此操作不可撤销！")
            confirm_col1, confirm_col2, _ = st.columns([1, 1, 2])
            with confirm_col1:
                if st.button("✅ 确认删除", type="primary"):
                    success, msg = batch_delete_users(st.session_state['confirm_batch_delete'])
                    if success:
                        # 清除缓存，刷新数据
                        get_users.clear()
                        st.success(msg)
                        st.session_state['confirm_batch_delete'] = None
                        st.session_state['selected_user_ids'] = []
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
            with confirm_col2:
                if st.button("❌ 取消"):
                    st.session_state['confirm_batch_delete'] = None
                    st.rerun()
        
        st.markdown("---")
        
        # ==================== 单个用户操作 ====================
        st.markdown("### 🔧 单个用户操作")
        
        # 创建用户选项
        user_options = {
            u['id']: f"{u.get('username', 'N/A')} (ID: {u['id']}) - {u.get('role', 'N/A')}"
            for u in other_users
        }
        
        op_col1, op_col2 = st.columns([2, 1])
        
        with op_col1:
            selected_user_id = st.selectbox(
                "选择用户",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                key="user_select"
            )
        
        selected_user = next((u for u in users if u['id'] == selected_user_id), None)
        
        # 检查是否为超级管理员（双重保护）
        if selected_user and selected_user.get('role') == 'super_admin':
            st.error("⚠️ 管理员不能管理超级管理员")
            st.stop()
        
        # 操作按钮行
        btn_row1 = st.columns([1, 1, 1, 1, 1, 1])
        
        with btn_row1[0]:
            if st.button("✏️ 编辑用户", type="primary", use_container_width=True):
                if selected_user and selected_user.get('role') == 'super_admin':
                    st.error("⚠️ 管理员不能编辑超级管理员")
                else:
                    st.session_state['show_edit_user'] = selected_user_id
        
        with btn_row1[1]:
            if st.button("🔄 切换状态", use_container_width=True):
                success, result = toggle_user_status(selected_user_id)
                if success:
                    st.success(result.get("message", "状态已切换"))
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result)
        
        with btn_row1[2]:
            if st.button("🔑 重置密码", use_container_width=True):
                if selected_user and selected_user.get('role') == 'super_admin':
                    st.error("⚠️ 管理员不能重置超级管理员密码")
                else:
                    st.session_state['show_reset_password'] = selected_user_id
        
        with btn_row1[3]:
            if st.button("🔓 解锁账户", use_container_width=True):
                if selected_user and selected_user.get('role') == 'super_admin':
                    st.error("⚠️ 管理员不能管理超级管理员")
                else:
                    st.session_state['show_unlock'] = selected_user_id
        
        with btn_row1[4]:
            if st.button("📋 登录历史", use_container_width=True):
                st.session_state['show_login_history'] = selected_user_id
        
        with btn_row1[5]:
            if st.button("🗑️ 删除用户", type="secondary", use_container_width=True):
                if selected_user and selected_user.get('role') == 'super_admin':
                    st.error("⚠️ 管理员不能删除超级管理员")
                else:
                    st.session_state['confirm_delete'] = selected_user_id
        
        # 编辑用户表单
        if st.session_state.get('show_edit_user') == selected_user_id and selected_user:
            with st.expander("✏️ 编辑用户信息", expanded=True):
                with st.form("edit_user_form"):
                    edit_email = st.text_input("邮箱", value=selected_user.get('email', ''))
                    edit_role = st.selectbox(
                        "角色",
                        ["teacher", "admin"],
                        index=0 if selected_user.get('role') == 'teacher' else 1
                    )
                    edit_unit = st.text_input("所属单位", value=selected_user.get('unit', ''))
                    edit_class = st.text_input("负责班级", value=selected_user.get('class_name', ''))
                    edit_is_active = st.checkbox("启用账户", value=selected_user.get('is_active', True))
                    
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        if st.form_submit_button("✅ 保存修改", type="primary", use_container_width=True):
                            update_data = {
                                "email": edit_email,
                                "role": edit_role,
                                "unit": edit_unit,
                                "class_name": edit_class,
                                "is_active": edit_is_active
                            }
                            success, msg = update_user(selected_user_id, update_data)
                            if success:
                                # 清除缓存，刷新数据
                                get_users.clear()
                                st.success(msg)
                                st.session_state['show_edit_user'] = None
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(msg)
                    with edit_col2:
                        if st.form_submit_button("❌ 取消", use_container_width=True):
                            st.session_state['show_edit_user'] = None
                            st.rerun()
        
        # 删除确认
        if st.session_state.get('confirm_delete') == selected_user_id:
            st.warning(f"⚠️ 确定要删除用户 **{user_options[selected_user_id]}** 吗？此操作不可撤销！")
            confirm_col1, confirm_col2, _ = st.columns([1, 1, 2])
            with confirm_col1:
                if st.button("✅ 确认删除", type="primary", key="confirm_delete_btn"):
                    if delete_user(selected_user_id):
                        st.success("用户已删除")
                        st.session_state['confirm_delete'] = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("删除失败")
            with confirm_col2:
                if st.button("❌ 取消", key="cancel_delete_btn"):
                    st.session_state['confirm_delete'] = None
                    st.rerun()
        
        # 重置密码表单
        if st.session_state.get('show_reset_password') == selected_user_id:
            with st.expander("🔑 重置密码", expanded=True):
                with st.form("reset_password_form"):
                    st.markdown(f"**重置 {user_options[selected_user_id]} 的密码**")
                    new_pwd = st.text_input("新密码（至少8位）", type="password")
                    confirm_pwd = st.text_input("确认密码", type="password")
                    
                    reset_col1, reset_col2 = st.columns(2)
                    with reset_col1:
                        if st.form_submit_button("✅ 确认重置", type="primary", use_container_width=True):
                            if len(new_pwd) < 8:
                                st.error("密码至少8位")
                            elif new_pwd != confirm_pwd:
                                st.error("两次密码不一致")
                            else:
                                if USE_BACKEND_API:
                                    try:
                                        response = requests.post(
                                            f"{API_BASE_URL}/admin/users/{selected_user_id}/reset-password",
                                            params={"new_password": new_pwd},
                                            headers=get_api_headers()
                                        )
                                        if response.status_code == 200:
                                            st.success("密码已重置")
                                            st.session_state['show_reset_password'] = None
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("重置失败")
                                    except:
                                        st.error("请求失败")
                                else:
                                    st.success("密码已重置 (Mock)")
                                    st.session_state['show_reset_password'] = None
                                    st.rerun()
                    with reset_col2:
                        if st.form_submit_button("❌ 取消", use_container_width=True):
                            st.session_state['show_reset_password'] = None
                            st.rerun()
        
        # 解锁账户（清除登录失败记录）
        if st.session_state.get('show_unlock') == selected_user_id:
            with st.expander("🔓 解锁账户", expanded=True):
                st.markdown(f"**清除 {user_options[selected_user_id]} 的登录失败记录**")
                st.info("此操作将清除该用户的所有登录失败记录，解除账户锁定。")
                
                unlock_col1, unlock_col2 = st.columns(2)
                with unlock_col1:
                    if st.button("✅ 确认解锁", type="primary", use_container_width=True, key="confirm_unlock"):
                        if USE_BACKEND_API:
                            try:
                                response = requests.delete(
                                    f"{API_BASE_URL}/admin/login-attempts/{selected_user.get('username', '')}",
                                    headers=get_api_headers()
                                )
                                if response.status_code == 200:
                                    st.success(response.json().get("message", "账户已解锁"))
                                    st.session_state['show_unlock'] = None
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    error_msg = response.json().get("detail", "解锁失败")
                                    st.error(error_msg)
                            except Exception as e:
                                st.error(f"请求失败: {str(e)}")
                        else:
                            st.success("账户已解锁 (Mock)")
                            st.session_state['show_unlock'] = None
                            st.rerun()
                with unlock_col2:
                    if st.button("❌ 取消", use_container_width=True, key="cancel_unlock"):
                        st.session_state['show_unlock'] = None
                        st.rerun()
        
        # 查看登录历史
        if st.session_state.get('show_login_history') == selected_user_id:
            with st.expander("📋 登录历史", expanded=True):
                st.markdown(f"**{user_options[selected_user_id]} 的登录历史记录**")
                if USE_BACKEND_API:
                    try:
                        response = requests.get(
                            f"{API_BASE_URL}/admin/users/{selected_user_id}/login-history",
                            params={"limit": 50},
                            headers=get_api_headers()
                        )
                        if response.status_code == 200:
                            histories = response.json()
                            if histories:
                                df_history = pd.DataFrame(histories)
                                df_history['登录时间'] = pd.to_datetime(df_history['login_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
                                df_history['状态'] = df_history['status'].apply(lambda x: "✅ 成功" if x == "success" else "❌ 失败")
                                df_history['IP地址'] = df_history['ip_address']
                                df_history['失败原因'] = df_history['failure_reason'].fillna("-")
                                
                                st.dataframe(
                                    df_history[['登录时间', '状态', 'IP地址', '失败原因']],
                                    use_container_width=True,
                                    hide_index=True
                                )
                            else:
                                st.info("暂无登录历史记录")
                        else:
                            st.error("获取登录历史失败")
                    except Exception as e:
                        st.error(f"请求失败: {str(e)}")
                else:
                    st.info("Mock: 登录历史记录功能需要后端API支持")
                
                if st.button("❌ 关闭", use_container_width=True, key="close_history"):
                    st.session_state['show_login_history'] = None
                    st.rerun()
    else:
        st.info("没有其他用户可以操作")

else:
    st.info("暂无用户数据")