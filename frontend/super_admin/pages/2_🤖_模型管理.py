"""
模型管理 - 超级管理员
"""
import streamlit as st
import requests
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, get_api_headers, check_super_admin_auth

st.set_page_config(page_title="模型管理 - 超级管理员", page_icon="🤖", layout="wide")

load_css()

# ==================== 权限检查 ====================
check_super_admin_auth()

render_sidebar()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.title("🤖 模型管理")

# ==================== 数据获取函数 ====================
@st.cache_data(ttl=60, show_spinner=False)
def get_model_info(_headers_tuple):
    """获取模型信息"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/super-admin/model-info",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

def update_model(model_name):
    """更新模型"""
    try:
        headers = get_api_headers()
        response = requests.post(
            f"{API_BASE_URL}/super-admin/model/update",
            headers=headers,
            json={"model_name": model_name},
            timeout=10
        )
        if response.status_code == 200:
            return True, response.json()
        return False, response.json().get("detail", "更新失败")
    except Exception as e:
        return False, str(e)

def activate_model(model_name):
    """激活模型"""
    try:
        headers = get_api_headers()
        response = requests.post(
            f"{API_BASE_URL}/super-admin/model/activate",
            headers=headers,
            json={"model_name": model_name},
            timeout=10
        )
        if response.status_code == 200:
            return True, response.json()
        return False, response.json().get("detail", "激活失败")
    except Exception as e:
        return False, str(e)

# ==================== 页面内容 ====================
headers_tuple = tuple(get_api_headers().items())
model_info = get_model_info(headers_tuple)

if not model_info:
    st.error("无法获取模型信息，请检查后端服务是否正常运行")
    st.stop()

# 当前配置
st.subheader("📋 当前模型配置")

config_col1, config_col2, config_col3 = st.columns(3)

with config_col1:
    st.info(f"**模型目录**: `{model_info.get('model_directory', 'N/A')}`")

with config_col2:
    st.info(f"**置信度阈值**: {model_info.get('current_config', {}).get('confidence_threshold', 'N/A')}")

with config_col3:
    st.info(f"**NMS IoU 阈值**: {model_info.get('current_config', {}).get('nms_iou_threshold', 'N/A')}")

st.divider()

# 模型列表
st.subheader("📦 模型列表")

models = model_info.get("models", [])

if models:
    import pandas as pd
    
    models_data = []
    for model in models:
        size_mb = model.get("size", 0) / (1024 * 1024)
        modified_time = datetime.fromtimestamp(model.get("modified", 0))
        models_data.append({
            "模型名称": model.get("name", "N/A"),
            "大小 (MB)": f"{size_mb:.2f}",
            "修改时间": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
            "路径": model.get("path", "N/A")
        })
    
    df = pd.DataFrame(models_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 模型操作
    st.markdown("### 🔧 模型操作")
    
    model_names = [m.get("name", "") for m in models]
    if model_names:
        selected_model = st.selectbox("选择模型", model_names, key="selected_model")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 更新模型", use_container_width=True, key="update_model"):
                with st.spinner("正在更新模型..."):
                    success, result = update_model(selected_model)
                    if success:
                        st.success("模型更新请求已提交")
                        st.info(result.get("message", ""))
                    else:
                        st.error(f"更新失败: {result}")
        
        with col2:
            if st.button("✅ 激活模型", use_container_width=True, key="activate_model"):
                with st.spinner("正在激活模型..."):
                    success, result = activate_model(selected_model)
                    if success:
                        st.success("模型激活请求已提交")
                        st.info(result.get("message", ""))
                    else:
                        st.error(f"激活失败: {result}")
else:
    st.warning("未找到模型文件")

st.divider()

# 功能说明
st.subheader("📖 功能说明")

st.markdown("""
**模型管理功能**：

1. **查看模型信息**
   - 显示所有可用的模型文件
   - 显示模型大小和修改时间
   - 显示当前模型配置

2. **更新模型**
   - 下载并更新模型文件
   - 验证模型文件完整性
   - 替换旧版本模型

3. **激活模型**
   - 切换系统使用的模型
   - 验证模型兼容性
   - 重启服务使新模型生效

**注意事项**：
- 模型更新需要验证文件完整性
- 激活新模型前请确保模型文件正确
- 模型切换可能需要重启服务
- 建议在低峰期进行模型更新操作
""")

st.warning("""
**开发中**：

模型更新和激活功能当前处于开发阶段。实际实现需要：

1. 模型下载和验证机制
2. 模型文件完整性检查
3. 模型版本管理
4. 服务重启机制

当前版本仅提供模型信息查看功能。
""")

