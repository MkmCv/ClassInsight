import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# 将父目录加入 path 以便导入 mock_data 和 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_data import MOCK_VIDEOS, get_mock_summary, get_mock_timeline, get_mock_anomalies
from utils import load_css

st.set_page_config(page_title="行为分析 - ClassInsight", page_icon="📈", layout="wide")

load_css()

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

# 侧边栏
with st.sidebar:
    st.markdown("### 🔍 筛选条件")
    video_options = {v['video_id']: f"{v['lesson_date']} {v['course_name']} ({v['class_name']})" for v in MOCK_VIDEOS}
    selected_video_id = st.selectbox(
        "选择课堂记录",
        options=list(video_options.keys()),
        format_func=lambda x: video_options[x]
    )
    st.caption("选择不同的课堂记录以查看详细分析。")

# 获取数据
summary_data = get_mock_summary(selected_video_id)
timeline_data = get_mock_timeline(selected_video_id)
anomalies_data = get_mock_anomalies(selected_video_id)

st.markdown(f"# 📈 课堂行为分析报告")
st.caption(f"分析对象: {video_options[selected_video_id]}")

# Tab 布局
tab1, tab2, tab3 = st.tabs(["📊 整课概览", "📉 时间趋势", "⚠️ 异常诊断"])

# ==================== Tab 1 ====================
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 关键指标
    student_behaviors = summary_data['behavior_summary']
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("互动总时长", f"{student_behaviors['discuss']['total_duration']}s", "正常")
    with c2:
        st.metric("举手次数", f"{student_behaviors['hand-raising']['count']}次", "-2次")
    with c3:
        st.metric("平均专注度", "85%", "+3%")
    with c4:
        st.metric("低头率", f"{student_behaviors['BowHead']['percentage']}%", "偏高", delta_color="inverse")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 学生行为分布")
        df_student = pd.DataFrame([
            {"行为": k, "时长": v["total_duration"]} 
            for k, v in student_behaviors.items()
        ])
        fig = px.pie(df_student, values='时长', names='行为', hole=0.6, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("### 教师行为分布")
        teacher_behaviors = summary_data['teacher_behavior']
        df_teacher = pd.DataFrame([
            {"行为": k, "时长": v["duration"]} 
            for k, v in teacher_behaviors.items()
        ])
        fig2 = px.pie(df_teacher, values='时长', names='行为', hole=0.6, color_discrete_sequence=px.colors.qualitative.Set3)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

# ==================== Tab 2 ====================
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 课堂状态演变趋势")
    
    timeline_list = timeline_data['timeline']
    df_timeline = pd.DataFrame([
        {"时间(分)": item['timestamp'] / 60, **item['behaviors']}
        for item in timeline_list
    ])
    
    all_behaviors = list(timeline_list[0]['behaviors'].keys())
    selected = st.multiselect("选择展示行为", all_behaviors, default=['discuss', 'read', 'BowHead'])
    
    fig_line = px.line(df_timeline, x="时间(分)", y=selected, markers=False, color_discrete_sequence=px.colors.qualitative.Bold)
    fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified")
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("### 课堂注意力热力图")
    fig_area = px.area(df_timeline, x="时间(分)", y=all_behaviors, color_discrete_sequence=px.colors.qualitative.Safe)
    fig_area.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_area, use_container_width=True)

# ==================== Tab 3 ====================
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### ⚠️ 异常事件列表")
        for anomaly in anomalies_data['anomalies']:
            start = anomaly['start_time'] // 60
            end = anomaly['end_time'] // 60
            color = "#EF4444" if anomaly['severity'] == "high" else "#F59E0B" if anomaly['severity'] == "medium" else "#3B82F6"
            
            st.markdown(f"""
            <div style="border-left: 4px solid {color}; padding-left: 12px; margin-bottom: 16px; background-color: #FFFFFF; padding: 16px; border-radius: 0 8px 8px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="font-weight: 600; font-size: 1.1rem; color: #111827;">{anomaly['description']}</div>
                <div style="color: #6B7280; font-size: 0.9rem; margin-top: 4px;">
                    <span style="background-color: {color}20; color: {color}; padding: 2px 8px; border-radius: 4px; font-weight: 500;">{anomaly['severity'].upper()}</span>
                    &nbsp; • &nbsp; {start}分 - {end}分
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_right:
        st.markdown("### 🔗 归因分析")
        st.info("💡 **AI 洞察**：分析发现，教师的“引导”行为与学生的“讨论”行为存在显著正相关 (Corr: 0.75)。")
        
        mock_corr = pd.DataFrame(
            [[1.0, 0.75, -0.2], [0.75, 1.0, -0.1], [-0.2, -0.1, 1.0]],
            columns=['引导', '讨论', '低头'],
            index=['引导', '讨论', '低头']
        )
        fig_corr = px.imshow(mock_corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
        fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_corr, use_container_width=True)
