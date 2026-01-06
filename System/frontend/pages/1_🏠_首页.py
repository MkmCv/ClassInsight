import streamlit as st
import sys
import os
import requests
from datetime import datetime, date, timedelta

# 修复路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, get_api_headers
from mock_data import MOCK_VIDEOS

st.set_page_config(page_title="首页 - ClassInsight", page_icon="🏠", layout="wide")

load_css()

# 检查登录
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.switch_page("app.py")

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
USE_BACKEND_API = True

# ==================== 侧边栏 ====================
render_sidebar()

# ==================== 数据获取函数 ====================
@st.cache_data(ttl=60)
def fetch_week_schedule(_headers, target_date_str):
    """获取周课表"""
    if not USE_BACKEND_API:
        # Mock数据
        return {
            "week_start": "2025-01-06",
            "week_end": "2025-01-12",
            "days": [
                {"date": "2025-01-06", "day_of_week": 0, "day_name": "星期一", "schedules": [
                    {"id": 1, "course_name": "数学(代数)", "class_name": "高一(1)班", 
                     "start_time": "08:00:00", "end_time": "08:45:00", "status": "finished"},
                    {"id": 2, "course_name": "数学(几何)", "class_name": "高一(3)班", 
                     "start_time": "10:00:00", "end_time": "10:45:00", "status": "ongoing"},
                ], "schedule_date": "2025-01-06"},
                {"date": "2025-01-07", "day_of_week": 1, "day_name": "星期二", "schedules": [
                    {"id": 3, "course_name": "数学(习题)", "class_name": "高一(2)班", 
                     "start_time": "14:00:00", "end_time": "14:45:00", "status": "upcoming"},
                ], "schedule_date": "2025-01-07"},
                {"date": "2025-01-08", "day_of_week": 2, "day_name": "星期三", "schedules": [], "schedule_date": "2025-01-08"},
                {"date": "2025-01-09", "day_of_week": 3, "day_name": "星期四", "schedules": [
                    {"id": 4, "course_name": "高等数学", "class_name": "高一(1)班", 
                     "start_time": "09:00:00", "end_time": "09:45:00", "status": "upcoming"},
                ], "schedule_date": "2025-01-09"},
                {"date": "2025-01-10", "day_of_week": 4, "day_name": "星期五", "schedules": [], "schedule_date": "2025-01-10"},
                {"date": "2025-01-11", "day_of_week": 5, "day_name": "星期六", "schedules": [], "schedule_date": "2025-01-11"},
                {"date": "2025-01-12", "day_of_week": 6, "day_name": "星期日", "schedules": [], "schedule_date": "2025-01-12"},
            ]
        }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/schedules/week",
            headers=_headers,
            params={"target_date": target_date_str},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=60)
def fetch_today_schedule(_headers):
    """获取今日课表"""
    if not USE_BACKEND_API:
        return [
            {"id": 1, "course_name": "数学(代数)", "class_name": "高一(1)班", 
             "start_time": "08:00:00", "end_time": "08:45:00", "status": "finished"},
            {"id": 2, "course_name": "数学(几何)", "class_name": "高一(3)班", 
             "start_time": "10:00:00", "end_time": "10:45:00", "status": "ongoing"},
            {"id": 3, "course_name": "数学(习题)", "class_name": "高一(2)班", 
             "start_time": "14:00:00", "end_time": "14:45:00", "status": "upcoming"},
        ]
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/schedules/today",
            headers=_headers,
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def fetch_dashboard_metrics():
    """获取首页指标数据"""
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
        return None
    except:
        return None


# ========== 顶部欢迎区 ==========
current_hour = datetime.now().hour
greeting = "早上好" if 5 <= current_hour < 12 else "下午好" if 12 <= current_hour < 18 else "晚上好"

col_header, col_date = st.columns([3, 1])
with col_header:
    username = st.session_state.get('user', {}).get('username', '用户')
    st.markdown(f"# {greeting}, {username} 👋")
    st.markdown("今天是教学的第 12 周，保持这种出色的状态！")
with col_date:
    st.markdown(f"<div style='text-align: right; color: #6B7280; font-size: 1.1rem; padding-top: 10px;'>{datetime.now().strftime('%Y-%m-%d %A')}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== 智能课表日历区 ==========
st.markdown("### 📅 智能课表日历")

# 日期选择器
col_picker, col_nav, col_spacer = st.columns([2, 2, 4])

with col_picker:
    selected_date = st.date_input(
        "选择日期",
        value=date.today(),
        key="calendar_date",
        label_visibility="collapsed"
    )

with col_nav:
    nav_col1, nav_col2, nav_col3 = st.columns(3)
    with nav_col1:
        if st.button("◀ 上周", use_container_width=True):
            st.session_state['calendar_date'] = selected_date - timedelta(days=7)
            st.rerun()
    with nav_col2:
        if st.button("今天", use_container_width=True):
            st.session_state['calendar_date'] = date.today()
            st.rerun()
    with nav_col3:
        if st.button("下周 ▶", use_container_width=True):
            st.session_state['calendar_date'] = selected_date + timedelta(days=7)
            st.rerun()

# 获取周课表数据
headers_tuple = tuple(sorted(get_api_headers().items()))
week_data = fetch_week_schedule(headers_tuple, selected_date.isoformat())

if week_data:
    # 显示周范围
    st.markdown(f"**{week_data.get('week_start', '')} 至 {week_data.get('week_end', '')}**")
    
    # 创建7列显示一周课表
    day_cols = st.columns(7)
    
    today = date.today()
    
    for idx, day in enumerate(week_data.get('days', [])):
        with day_cols[idx]:
            day_date = day.get('date', '')
            day_name = day.get('day_name', '')
            schedules = day.get('schedules', [])
            
            # 判断是否是今天
            is_today = day_date == today.isoformat()
            
            # 日期标题样式
            if is_today:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; padding: 8px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                    <div style="font-weight: 600;">{day_name}</div>
                    <div style="font-size: 0.8rem;">{day_date}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f3f4f6; padding: 8px; border-radius: 8px; text-align: center; margin-bottom: 8px;">
                    <div style="font-weight: 600; color: #374151;">{day_name}</div>
                    <div style="font-size: 0.8rem; color: #6b7280;">{day_date}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 显示当天课程
            if schedules:
                for s in schedules:
                    status = s.get('status', 'upcoming')
                    
                    if status == 'finished':
                        bg = "#f3f4f6"
                        border = "#9ca3af"
                        text_color = "#6b7280"
                        badge = "✓ 已结束"
                        badge_bg = "#e5e7eb"
                    elif status == 'ongoing':
                        bg = "#eef2ff"
                        border = "#4f46e5"
                        text_color = "#312e81"
                        badge = "● 进行中"
                        badge_bg = "#c7d2fe"
                    else:
                        bg = "#ecfdf5"
                        border = "#10b981"
                        text_color = "#065f46"
                        badge = "○ 待开始"
                        badge_bg = "#d1fae5"
                    
                    # 格式化时间
                    start = s.get('start_time', '')[:5] if s.get('start_time') else ''
                    end = s.get('end_time', '')[:5] if s.get('end_time') else ''
                    
                    st.markdown(f"""
                    <div style="background: {bg}; border-left: 3px solid {border}; 
                                padding: 8px; border-radius: 6px; margin-bottom: 6px;">
                        <div style="font-size: 0.75rem; color: {text_color};">{start}-{end}</div>
                        <div style="font-weight: 500; color: {text_color}; font-size: 0.9rem;">{s.get('course_name', '')}</div>
                        <div style="font-size: 0.75rem; color: {text_color};">📍 {s.get('class_name', '')}</div>
                        <div style="margin-top: 4px;">
                            <span style="background: {badge_bg}; color: {text_color}; 
                                         padding: 2px 6px; border-radius: 10px; font-size: 0.7rem;">{badge}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="color: #9ca3af; font-size: 0.85rem; text-align: center; padding: 20px 0;">
                    暂无课程
                </div>
                """, unsafe_allow_html=True)
else:
    st.info("📭 暂无课表数据，请联系管理员排课")

st.markdown("<br>", unsafe_allow_html=True)

# ========== 今日课程快览 + 智能提醒 ==========
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("### 📚 今日课程")
    today_schedules = fetch_today_schedule(headers_tuple)
    
    if today_schedules:
        cols = st.columns(min(3, len(today_schedules)))
        
        for idx, course in enumerate(today_schedules[:3]):
            with cols[idx]:
                status = course.get("status", "upcoming")
                
                if status == "finished":
                    bg_color = "#F3F4F6"
                    border_color = "#9CA3AF"
                    status_label = "已结束"
                elif status == "ongoing":
                    bg_color = "#EEF2FF"
                    border_color = "#4F46E5"
                    status_label = "进行中"
                else:
                    bg_color = "#ECFDF5"
                    border_color = "#10B981"
                    status_label = "待开始"
                
                start = course.get('start_time', '')[:5] if course.get('start_time') else '--'
                end = course.get('end_time', '')[:5] if course.get('end_time') else '--'
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-radius: 12px; padding: 16px; 
                            border-left: 4px solid {border_color}; height: 100%;">
                    <div style="font-size: 0.85rem; color: #6B7280;">{start} - {end}</div>
                    <div style="font-weight: 600; font-size: 1.1rem; margin: 4px 0; color: #374151;">
                        {course.get('course_name', '--')}
                    </div>
                    <div style="font-size: 0.9rem; color: #4B5563;">📍 {course.get('class_name', '--')}</div>
                    <div style="margin-top: 8px;">
                        <span style="background-color: {border_color}20; padding: 2px 8px; 
                                     border-radius: 12px; font-size: 0.75rem; color: {border_color};">
                            {status_label}
                        </span>
                    </div>
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

metrics_data = fetch_dashboard_metrics()

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
    with m1:
        st.metric("平均互动率", "N/A", help="后端服务未连接")
    with m2:
        st.metric("课堂专注度", "N/A", help="后端服务未连接")
    with m3:
        st.metric("教学节奏", "N/A", help="后端服务未连接")
    with m4:
        st.metric("待处理视频", "N/A", help="后端服务未连接")

# ========== 快捷功能区 ==========
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 🚀 常用功能")

col_upload, col_analysis, col_opt = st.columns(3)

with col_upload:
    st.markdown("#### 📤 上传课堂视频")
    st.markdown("课后及时上传录像，获取AI分析报告。")
    if st.button("去上传", key="home_upload", use_container_width=True):
        st.switch_page("pages/2_📤_视频上传.py")

with col_analysis:
    st.markdown("#### 📊 课堂行为分析")
    st.markdown("深入查看每节课的学生行为分布与异常。")
    if st.button("看报表", key="home_analysis", use_container_width=True):
        st.switch_page("pages/3_📈_行为分析.py")

with col_opt:
    st.markdown("#### 💡 教学改进建议")
    st.markdown("基于数据的个性化建议，助您提升教学质量。")
    if st.button("获建议", key="home_opt", use_container_width=True):
        st.switch_page("pages/4_💡_教学建议.py")