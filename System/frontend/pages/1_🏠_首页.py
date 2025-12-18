import streamlit as st
import sys
import os
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

# 侧边栏
with st.sidebar:
    st.markdown("### 🔍 快速导航")
    st.info("欢迎使用 ClassInsight 教学分析系统")
    
# ========== 顶部欢迎区 ==========
current_hour = datetime.now().hour
greeting = "早上好" if 5 <= current_hour < 12 else "下午好" if 12 <= current_hour < 18 else "晚上好"

col_header, col_date = st.columns([3, 1])
with col_header:
    st.markdown(f"# {greeting}, {st.session_state['user']['username']} 👋")
    st.markdown("今天是教学的第 12 周，保持这种出色的状态！")
with col_date:
    st.markdown(f"<div style='text-align: right; color: #6B7280; font-size: 1.1rem; padding-top: 10px;'>{datetime.now().strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ========== 智能提醒与下节课 ==========
c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("### 📅 今日课程 (Today's Schedule)")
    sc1, sc2, sc3 = st.columns(3)
    
    with sc1:
        st.markdown("""
        <div style="background-color: #F3F4F6; border-radius: 12px; padding: 16px; border-left: 4px solid #9CA3AF; height: 100%;">
            <div style="font-size: 0.85rem; color: #6B7280;">08:00 - 08:45</div>
            <div style="font-weight: 600; font-size: 1.1rem; margin: 4px 0; color: #374151;">数学 (代数)</div>
            <div style="font-size: 0.9rem; color: #4B5563;">📍 高一(1)班</div>
            <div style="margin-top: 8px;"><span style="background-color: #E5E7EB; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; color: #6B7280;">已结束</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with sc2:
        st.markdown("""
        <div style="background-color: #EEF2FF; border-radius: 12px; padding: 16px; border-left: 4px solid #4F46E5; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); height: 100%;">
            <div style="font-size: 0.85rem; color: #4F46E5; font-weight: 600;">10:00 - 10:45 (Next)</div>
            <div style="font-weight: 700; font-size: 1.1rem; margin: 4px 0; color: #111827;">数学 (几何)</div>
            <div style="font-size: 0.9rem; color: #4B5563;">📍 高一(3)班</div>
            <div style="margin-top: 8px;">
                <span style="background-color: #C7D2FE; color: #312E81; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">🔔 15分钟后</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with sc3:
        st.markdown("""
        <div style="background-color: white; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; border-left: 4px solid #10B981; height: 100%;">
            <div style="font-size: 0.85rem; color: #6B7280;">14:00 - 14:45</div>
            <div style="font-weight: 600; font-size: 1.1rem; margin: 4px 0; color: #111827;">数学 (习题)</div>
            <div style="font-size: 0.9rem; color: #4B5563;">📍 高一(2)班</div>
            <div style="margin-top: 8px;"><span style="background-color: #ECFDF5; color: #065F46; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem;">下午</span></div>
        </div>
        """, unsafe_allow_html=True)

with c2:
    st.markdown("### 🔔 智能提醒")
    st.info("📝 **备课提醒**：下节课是《立体几何》，建议准备3D模型教具。")
    st.warning("⚠️ **关注名单**：高一(3)班的张同学昨日课堂低头率较高，请留意。")

st.markdown("<br>", unsafe_allow_html=True)

# ========== 核心数据概览 ==========
st.markdown("### 📈 近期课堂表现概览")

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("平均互动率", "35%", "+5%", help="学生参与讨论和回答问题的时间占比")
with m2:
    st.metric("课堂专注度", "88%", "+2%", help="学生注视黑板、屏幕或书本的时间占比")
with m3:
    st.metric("教学节奏", "适中", "Excellent", help="教师讲授与学生活动的比例")
with m4:
    st.metric("待处理视频", "2", "-1", delta_color="inverse", help="已上传但未完成分析的视频")

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


