import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import requests
import sys
import os
import time

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css

st.set_page_config(page_title="教学建议 - ClassInsight", page_icon="💡", layout="wide")

load_css()

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def get_api_headers():
    """获取带认证的请求头"""
    headers = {"Content-Type": "application/json"}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers


def fetch_video_list():
    """获取视频列表"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/videos",
            headers=get_api_headers(),
            params={"page": 1, "page_size": 50, "status": "completed"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("items", [])
        return []
    except:
        return []


def fetch_recommendations(video_id):
    """获取教学建议"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/optimization/{video_id}/recommendations",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def fetch_highlights(video_id):
    """获取精彩片段"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/optimization/{video_id}/highlights",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def fetch_comparison():
    """获取跨课次对比数据"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/optimization/comparison",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


# 获取视频列表
videos = fetch_video_list()

with st.sidebar:
    st.markdown("### 🔍 筛选条件")
    
    if videos:
        video_options = {v['video_id']: f"{v.get('lesson_date', 'N/A')} {v.get('course_name', '-')}" for v in videos}
        
        # 如果有当前视频ID，默认选中
        default_idx = 0
        if 'current_video_id' in st.session_state:
            try:
                video_ids = list(video_options.keys())
                if st.session_state['current_video_id'] in video_ids:
                    default_idx = video_ids.index(st.session_state['current_video_id'])
            except:
                pass
        
        selected_video_id = st.selectbox(
            "选择课堂记录", 
            list(video_options.keys()), 
            format_func=lambda x: video_options[x],
            index=default_idx
        )
    else:
        st.warning("暂无已分析视频")
        selected_video_id = None

# 获取数据
recommendations_data = fetch_recommendations(selected_video_id) if selected_video_id else None
highlights_data = fetch_highlights(selected_video_id) if selected_video_id else None
comparison_data = fetch_comparison()

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
        
        if recommendations_data and recommendations_data.get('recommendations'):
            for rec in recommendations_data['recommendations']:
                priority = rec.get('priority', 'medium')
                color = "#EF4444" if priority == 'high' else "#F59E0B" if priority == 'medium' else "#10B981"
                bg_color = "#FEF2F2" if priority == 'high' else "#FFFBEB" if priority == 'medium' else "#ECFDF5"
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border: 1px solid {color}40; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #111827;">{rec.get('title', '建议')}</h4>
                        <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{priority.upper()}</span>
                    </div>
                    <p style="color: #4B5563; margin-bottom: 16px;">{rec.get('description', '')}</p>
                    <div style="background-color: white; padding: 12px; border-radius: 6px; border: 1px solid {color}20;">
                        <div style="font-weight: 600; color: {color}; margin-bottom: 8px; font-size: 0.9rem;">🚀 建议行动：</div>
                        <ul style="margin: 0; padding-left: 20px; color: #4B5563; font-size: 0.95rem;">
                            {''.join([f'<li style="margin-bottom: 4px;">{action}</li>' for action in rec.get('suggested_actions', [])])}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # 默认建议（无数据时显示）
            default_recommendations = [
                {
                    'title': '提升课堂互动频率',
                    'priority': 'high',
                    'description': '根据分析，课堂互动时间占比低于推荐值，建议增加师生互动环节。',
                    'suggested_actions': ['每15分钟设置一个提问环节', '使用小组讨论激发学生参与', '鼓励学生主动举手发言']
                },
                {
                    'title': '关注后排学生',
                    'priority': 'medium',
                    'description': '后排学生的注意力数据显示专注度较低，建议加强关注。',
                    'suggested_actions': ['增加教室巡视频率', '适当走向教室后方授课', '随机抽问后排学生']
                }
            ]
            
            for rec in default_recommendations:
                priority = rec['priority']
                color = "#EF4444" if priority == 'high' else "#F59E0B" if priority == 'medium' else "#10B981"
                bg_color = "#FEF2F2" if priority == 'high' else "#FFFBEB" if priority == 'medium' else "#ECFDF5"
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border: 1px solid {color}40; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #111827;">{rec['title']}</h4>
                        <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{priority.upper()}</span>
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
        
        if highlights_data and highlights_data.get('highlights'):
            for highlight in highlights_data['highlights']:
                start = highlight.get('start_time', 0) // 60
                end = highlight.get('end_time', 0) // 60
                
                with st.container():
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.image("https://img.freepik.com/free-photo/students-knowing-right-answer_329181-14271.jpg", use_column_width=True)
                    with c2:
                        st.markdown(f"#### ⭐ 评分: {highlight.get('score', 'N/A')}")
                        st.caption(f"时段: {start}m - {end}m")
                        st.write(highlight.get('description', ''))
                        reasons = highlight.get('reasons', [])
                        if reasons:
                            st.info("入选理由: " + "、".join(reasons))
        else:
            st.info("📹 上传并分析视频后，将自动提取课堂精彩片段。")

    with col2:
        st.markdown("### 📊 跨课次教学能力模型")
        
        # 使用后端数据或默认数据
        if comparison_data and comparison_data.get('metrics'):
            categories = [m.get('name', '') for m in comparison_data['metrics']]
            current_values = [m.get('current', 0) for m in comparison_data['metrics']]
            average_values = [m.get('average', 0) for m in comparison_data['metrics']]
        else:
            categories = ['互动率', '专注度', '活跃度', '教师引导', '多媒体使用']
            current_values = [4.2, 3.5, 2.8, 4.5, 3.2]
            average_values = [3.8, 3.9, 3.2, 3.5, 2.9]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=current_values,
            theta=categories,
            fill='toself',
            name='本节课',
            line_color='#4F46E5'
        ))
        fig.add_trace(go.Scatterpolar(
            r=average_values,
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
        
        if comparison_data and comparison_data.get('history'):
            dates = [h.get('date', '') for h in comparison_data['history']]
            scores = [h.get('score', 0) for h in comparison_data['history']]
        else:
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
            
            # 模拟回复内容（后续可接入 AI Agent API）
            mock_response = f'''针对您提到的问题「{prompt}」，结合本节课的数据分析，我建议：

1. **引入间隔性活动**：在第30分钟设置一个「快速问答」环节，重新激活学生大脑。
2. **多媒体辅助**：数据显示，当您使用屏幕演示时（Screen行为），学生的抬头率会提升 40%。建议在后半段增加演示环节。
3. **走动教学**：热力图显示后排学生的低头率较高，建议您多走到教室后方进行巡视和互动。'''
            
            for chunk in mock_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
