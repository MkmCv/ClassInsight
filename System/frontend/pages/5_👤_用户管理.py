import streamlit as st
import requests
import sys
import os
import time
import pandas as pd
from datetime import datetime

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css
from mock_data import MOCK_USERS_LIST

st.set_page_config(page_title="用户管理 - ClassInsight", page_icon="👤", layout="wide")

# 引入 CSS
load_css()

# ==================== 权限检查 ====================
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

current_user = st.session_state.get('user', {})
if current_user.get('role') != 'admin':
    st.error("⚠️ 只有管理员可以访问此页面")
    st.stop()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
USE_BACKEND_API = False # 暂时默认为False，待后端实现后改为True

def get_api_headers():
    headers = {}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers

# ==================== 数据获取函数 ====================
def get_users():
    if USE_BACKEND_API:
        try:
            response = requests.get(f"{API_BASE_URL}/admin/users", headers=get_api_headers(), timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    else:
        return MOCK_USERS_LIST

def create_user(user_data):
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
        # 必须使用 global 修改 mock_data 里的引用，否则页面刷新后数据会还原
        # 注意：在多页面应用中，mock_data 模块会被缓存，但直接修改列表内容是生效的
        # 找到要删除的索引
        idx = -1
        for i, u in enumerate(MOCK_USERS_LIST):
            if u['id'] == user_id:
                idx = i
                break
        if idx != -1:
            del MOCK_USERS_LIST[idx]
            return True
        return False

# ==================== 页面布局 ====================
st.markdown("# 👤 用户管理")
st.markdown("管理系统用户（教师/管理员），注册新账号或维护现有信息。")
st.markdown("<br>", unsafe_allow_html=True)

# 顶部工具栏
col_tool_1, col_tool_2 = st.columns([3, 1])
with col_tool_2:
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
                        st.success(msg)
                        st.session_state['show_create_user_form'] = False
                        st.rerun()
                    else:
                        st.error(f"创建失败: {msg}")

# 用户列表展示
users = get_users()
if users:
    # 转换为DataFrame以便展示
    df = pd.DataFrame(users)
    
    # 自定义列名映射
    column_config = {
        "id": st.column_config.NumberColumn("ID", width="small"),
        "username": st.column_config.TextColumn("用户名", width="medium"),
        "role": st.column_config.TextColumn("角色", width="small"),
        "unit": st.column_config.TextColumn("所属单位", width="medium"),
        "class_name": st.column_config.TextColumn("负责班级", width="medium"),
        "email": st.column_config.TextColumn("邮箱", width="medium"),
        "created_at": st.column_config.DatetimeColumn("创建时间", format="D MMM YYYY, h:mm a"),
    }
    
    # 筛选展示的列
    display_cols = ["id", "username", "role", "unit", "class_name", "email", "created_at"]
    # 确保列存在
    display_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(
        df[display_cols],
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )
    
    # 用户操作区
    st.markdown("### 🔧 用户操作")
    
    # 构建用户选择下拉框（排除当前登录用户）
    other_users = [u for u in users if u.get('id') != current_user.get('id')]
    
    if other_users:
        # 创建用户选项：显示格式为 "用户名 (ID: x) - 角色"
        user_options = {
            u['id']: f"{u.get('username', 'N/A')} (ID: {u['id']}) - {u.get('role', 'N/A')}"
            for u in other_users
        }
        
        op_col1, op_col2, op_col3 = st.columns([2, 1, 1])
        
        with op_col1:
            selected_user_id = st.selectbox(
                "选择用户",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                key="user_select"
            )
        
        with op_col2:
            # 显示选中用户信息
            selected_user = next((u for u in users if u['id'] == selected_user_id), None)
            if selected_user:
                st.text_input("邮箱", value=selected_user.get('email', 'N/A'), disabled=True)
        
        with op_col3:
            st.text_input("单位", value=selected_user.get('unit', 'N/A') if selected_user else '', disabled=True)
        
        # 操作按钮
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 2])
        
        with btn_col1:
            if st.button("🗑️ 删除用户", type="secondary", use_container_width=True):
                st.session_state['confirm_delete'] = selected_user_id
        
        with btn_col2:
            if st.button("🔑 重置密码", type="secondary", use_container_width=True):
                st.session_state['show_reset_password'] = selected_user_id
        
        # 删除确认
        if st.session_state.get('confirm_delete') == selected_user_id:
            st.warning(f"⚠️ 确定要删除用户 **{user_options[selected_user_id]}** 吗？此操作不可撤销！")
            confirm_col1, confirm_col2, _ = st.columns([1, 1, 2])
            with confirm_col1:
                if st.button("✅ 确认删除", type="primary"):
                    if delete_user(selected_user_id):
                        st.success(f"用户已删除")
                        st.session_state['confirm_delete'] = None
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("删除失败")
            with confirm_col2:
                if st.button("❌ 取消"):
                    st.session_state['confirm_delete'] = None
                    st.rerun()
        
        # 重置密码表单
        if st.session_state.get('show_reset_password') == selected_user_id:
            with st.form("reset_password_form"):
                st.markdown(f"**重置 {user_options[selected_user_id]} 的密码**")
                new_pwd = st.text_input("新密码（至少8位）", type="password")
                confirm_pwd = st.text_input("确认密码", type="password")
                
                if st.form_submit_button("确认重置"):
                    if len(new_pwd) < 8:
                        st.error("密码至少8位")
                    elif new_pwd != confirm_pwd:
                        st.error("两次密码不一致")
                    else:
                        # 调用重置密码 API
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
                                else:
                                    st.error("重置失败")
                            except:
                                st.error("请求失败")
                        else:
                            st.success("密码已重置 (Mock)")
                            st.session_state['show_reset_password'] = None
    else:
        st.info("没有其他用户可以操作")

else:
    st.info("暂无用户数据")
