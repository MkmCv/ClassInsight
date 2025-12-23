import streamlit as st
import sys
import os
import requests
from datetime import datetime

# 修复路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css
from mock_data import MOCK_VIDEOS

st.set_page_config(page_title="首页 - ClassInsight", page_icon="🏠", layout="wide")

load_css()

# 检查登录
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.switch_page("app.py")

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
USE_BACKEND_API = True  # 设为 False 使用 Mock 数据


def get_api_headers():
    """获取带认证的请求头"""
    headers = {"Content-Type": "application/json"}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers


def fetch_dashboard_metrics():
    """从后端获取首页指标数据"""
    if not USE_BACKEND_API:
        return {
            "interaction_rate": {"value": "35%", "delta": "+5%"},
            "focus_rate": {"value": "88%", "delta": "+2%"},
            "pending_videos": 2
        }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/metrics",
            headers=get_api_headers(),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"获取指标数据失败: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        st.warning(f"请求错误: {e}")
        return None


def fetch_dashboard_schedule():
    """从后端获取今日课程表"""
    if not USE_BACKEND_API:
        return [
            {"time": "08:00 - 08:45", "subject": "数学 (代数)", "class": "高一(1)班", "status": "finished"},
            {"time": "10:00 - 10:45", "subject": "数学 (几何)", "class": "高一(3)班", "status": "ongoing"},
            {"time": "14:00 - 14:45", "subject": "数学 (习题)", "class": "高一(2)班", "status": "upcoming"}
        ]
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/schedule",
            headers=get_api_headers(),
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("schedule", [])
        return []
    except:
        return []


def fetch_recent_videos(limit=5):
    """从后端获取最近的视频列表"""
    if not USE_BACKEND_API:
        return MOCK_VIDEOS[:limit]
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/recent-videos",
            headers=get_api_headers(),
            params={"limit": limit},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("videos", [])
        return []
    except:
        return []


# 侧边栏
with st.sidebar:
    st.markdown("### 🔍 快速导航")
    st.info("欢迎使用 ClassInsight 教学分析系统")
    
# ========== 顶部欢迎区 ==========
current_hour = datetime.now().hour
greeting = "早上好" if 5 <= current_hour < 12 else "下午好" if 12 <= current_hour < 18 else "晚上好"

col_header, col_date = st.columns([3, 1])
with col_header:
    username = st.session_state.get('user', {}).get('username', '用户')
    st.markdown(f"# {greeting}, {username} 👋")
    st.markdown("今天是教学的第 12 周，保持这种出色的状态！")
with col_date:
    st.markdown(f"<div style='text-align: right; color: #6B7280; font-size: 1.1rem; padding-top: 10px;'>{datetime.now().strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== 获取数据 ==========
schedule_data = fetch_dashboard_schedule()
metrics_data = fetch_dashboard_metrics()

# ========== 智能提醒与下节课 ==========
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("### 📅 今日课程 (Today's Schedule)")
    
    if schedule_data:
        # 动态生成课程卡片
        cols = st.columns(min(3, len(schedule_data)))
        
        for idx, course in enumerate(schedule_data[:3]):
            with cols[idx]:
                status = course.get("status", "upcoming")
                
                if status == "finished":
                    bg_color = "#F3F4F6"
                    border_color = "#9CA3AF"
                    status_bg = "#E5E7EB"
                    status_text = "#6B7280"
                    status_label = "已结束"
                elif status == "ongoing":
                    bg_color = "#EEF2FF"
                    border_color = "#4F46E5"
                    status_bg = "#C7D2FE"
                    status_text = "#312E81"
                    status_label = "进行中"
                else:
                    bg_color = "white"
                    border_color = "#10B981"
                    status_bg = "#ECFDF5"
                    status_text = "#065F46"
                    status_label = "待开始"
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-radius: 12px; padding: 16px; border-left: 4px solid {border_color}; height: 100%;">
                    <div style="font-size: 0.85rem; color: #6B7280;">{course.get('time', '--')}</div>
                    <div style="font-weight: 600; font-size: 1.1rem; margin: 4px 0; color: #374151;">{course.get('subject', '--')}</div>
                    <div style="font-size: 0.9rem; color: #4B5563;">📍 {course.get('class', '--')}</div>
                    <div style="margin-top: 8px;"><span style="background-color: {status_bg}; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; color: {status_text};">{status_label}</span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("📭 今日暂无课程安排")

with c2:
    st.markdown("### 🔔 智能提醒")
    st.info("📝 **备课提醒**：下节课是《立体几何》，建议准备3D模型教具。")
    st.warning("⚠️ **关注名单**：高一(3)班的张同学昨日课堂低头率较高，请留意。")

st.markdown("<br>", unsafe_allow_html=True)

# ========== 核心数据概览 ==========
st.markdown("### 📈 近期课堂表现概览")

m1, m2, m3, m4 = st.columns(4)

if metrics_data:
    with m1:
        ir = metrics_data.get("interaction_rate", {})
        st.metric("平均互动率", ir.get("value", "N/A"), ir.get("delta", ""), help="学生参与讨论和回答问题的时间占比")
    with m2:
        fr = metrics_data.get("focus_rate", {})
        st.metric("课堂专注度", fr.get("value", "N/A"), fr.get("delta", ""), help="学生注视黑板、屏幕或书本的时间占比")
    with m3:
        st.metric("教学节奏", "适中", "Excellent", help="教师讲授与学生活动的比例")
    with m4:
        pending = metrics_data.get("pending_videos", 0)
        st.metric("待处理视频", str(pending), delta_color="inverse", help="已上传但未完成分析的视频")
else:
    # 后端不可用时显示占位
    with m1:
        st.metric("平均互动率", "N/A", help="后端服务未连接")
    with m2:
        st.metric("课堂专注度", "N/A", help="后端服务未连接")
    with m3:
        st.metric("教学节奏", "N/A", help="后端服务未连接")
    with m4:
        st.metric("待处理视频", "N/A", help="后端服务未连接")

# ========== 快捷功能区 (卡片式入口) ==========
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🚀 常用功能")

col_upload, col_analysis, col_opt = st.columns(3)

with col_upload:
    with st.container():
        st.markdown("#### 📤 上传课堂视频")
        st.markdown("课后及时上传录像，获取AI分析报告。")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("去上传", key="home_upload", use_container_width=True):
            st.switch_page("pages/2_📤_视频上传.py")
            
with col_analysis:
    with st.container():
        st.markdown("#### 📊 课堂行为分析")
        st.markdown("深入查看每节课的学生行为分布与异常。")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("看报表", key="home_analysis", use_container_width=True):
            st.switch_page("pages/3_📈_行为分析.py")
            
with col_opt:
    with st.container():
        st.markdown("#### 💡 教学改进建议")
        st.markdown("基于数据的个性化建议，助您提升教学质量。")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("获建议", key="home_opt", use_container_width=True):
            st.switch_page("pages/4_💡_教学建议.py")


