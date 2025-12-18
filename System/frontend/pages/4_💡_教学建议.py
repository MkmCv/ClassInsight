import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
import time

# 将父目录加入 path 以便导入 mock_data 和 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mock_data import MOCK_VIDEOS, get_mock_recommendations, get_mock_highlights
from utils import load_css

st.set_page_config(page_title="教学建议 - ClassInsight", page_icon="💡", layout="wide")

load_css()

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

with st.sidebar:
    st.markdown("### 🔍 筛选条件")
    video_options = {v['video_id']: f"{v['lesson_date']} {v['course_name']}" for v in MOCK_VIDEOS}
    selected_video_id = st.selectbox("选择课堂记录", list(video_options.keys()), format_func=lambda x: video_options[x])

recommendations = get_mock_recommendations(selected_video_id)
highlights = get_mock_highlights(selected_video_id)

st.markdown("# 💡 AI 教学优化助手")
st.markdown("基于多维数据分析，为您提供个性化的教学改进建议。")
st.markdown("<br>", unsafe_allow_html=True)

# 创建两个 Tab：一个是常规建议，一个是 AI 深度对话
tab1, tab2 = st.tabs(["📝 综合诊断报告", "🤖 AI 教学顾问"])

# ==================== Tab 1: 综合诊断 ====================
with tab1:
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("### 🎯 改进建议")
        
        for rec in recommendations['recommendations']:
            color = "#EF4444" if rec['priority'] == 'high' else "#F59E0B" if rec['priority'] == 'medium' else "#10B981"
            bg_color = "#FEF2F2" if rec['priority'] == 'high' else "#FFFBEB" if rec['priority'] == 'medium' else "#ECFDF5"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; border: 1px solid {color}40; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #111827;">{rec['title']}</h4>
                    <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{rec['priority'].upper()}</span>
                </div>
                <p style="color: #4B5563; margin-bottom: 16px;">{rec['description']}</p>
                <div style="background-color: white; padding: 12px; border-radius: 6px; border: 1px solid {color}20;">
                    <div style="font-weight: 600; color: {color}; margin-bottom: 8px; font-size: 0.9rem;">🚀 建议行动：</div>
                    <ul style="margin: 0; padding-left: 20px; color: #4B5563; font-size: 0.95rem;">
                        {''.join([f'<li style="margin-bottom: 4px;">{action}</li>' for action in rec['suggested_actions']])}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🎬 精彩片段回顾")
        for highlight in highlights['highlights']:
            start = highlight['start_time'] // 60
            end = highlight['end_time'] // 60
            
            with st.container():
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.image("https://img.freepik.com/free-photo/students-knowing-right-answer_329181-14271.jpg", use_column_width=True)
                with c2:
                    st.markdown(f"#### ⭐ 评分: {highlight['score']}")
                    st.caption(f"时段: {start}m - {end}m")
                    st.write(highlight['description'])
                    st.info("入选理由: " + "、".join(highlight['reasons']))

    with col2:
        st.markdown("### 📊 跨课次教学能力模型")
        
        categories = ['互动率', '专注度', '活跃度', '教师引导', '多媒体使用']
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[4.2, 3.5, 2.8, 4.5, 3.2],
            theta=categories,
            fill='toself',
            name='本节课',
            line_color='#4F46E5'
        ))
        fig.add_trace(go.Scatterpolar(
            r=[3.8, 3.9, 3.2, 3.5, 2.9],
            theta=categories,
            fill='toself',
            name='历史平均',
            line_color='#9CA3AF',
            line_dash='dot'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 5], gridcolor="#E5E7EB"),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### 📈 历史趋势")
        dates = ['10-01', '10-08', '10-15', '10-22', '10-29']
        scores = [7.5, 7.8, 8.2, 8.0, 8.5]
        
        fig2 = px.line(x=dates, y=scores, markers=True, title="教学质量评分趋势")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis_range=[0, 10])
        st.plotly_chart(fig2, use_container_width=True)

# ==================== Tab 2: AI 教学顾问 ====================
with tab2:
    st.markdown("""
    <div style="background-color: #EEF2FF; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <h4 style="color: #4338CA; margin: 0;">🤖 AI 教学顾问</h4>
        <p style="color: #4B5563; margin-top: 8px;">我是基于大模型的教学助手。我已经阅读了本节课的所有行为数据，您可以问我任何关于教学改进的问题。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 聊天历史 Session
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "您好！看了这节课的数据，我发现学生的互动率比上周提升了 5%，但在课程后半段（第35分钟左右）有明显的注意力下降。您想针对这一点讨论改进策略吗？"}
        ]

    # 显示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 输入框
    if prompt := st.chat_input("请输入您的问题（例如：如何提高后半段的学生专注度？）"):
        # 用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 回复（模拟流式输出）
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 模拟思考过程
            with st.spinner("AI 正在思考教学策略..."):
                time.sleep(1.5)
            
            # 模拟回复内容（后续这里接真实 API）
            mock_response = f"针对您提到的问题“{prompt}”，结合本节课的数据分析，我建议：\n\n1. **引入间隔性活动**：在第30分钟设置一个“快速问答”环节，重新激活学生大脑。\n2. **多媒体辅助**：数据显式，当您使用屏幕演示时（Screen行为），学生的抬头率会提升 40%。建议在后半段增加演示环节。\n3. **走动教学**：热力图显示后排学生的低头率较高，建议您多走到教室后方进行巡视和互动。"
            
            for chunk in mock_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})


