import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import requests
import sys
import os
import time

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar

st.set_page_config(page_title="教学建议 - ClassInsight", page_icon="💡", layout="wide")

load_css()

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

# 渲染侧边栏（用户信息 + 退出登录）
render_sidebar()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def get_api_headers():
    """获取带认证的请求头"""
    headers = {"Content-Type": "application/json"}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers


@st.cache_data(ttl=30, show_spinner=False)
def fetch_video_list(_headers_tuple):
    """获取视频列表（缓存30秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/videos",
            headers=headers,
            params={"page": 1, "page_size": 50, "status": "completed"},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("items", [])
        return []
    except:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_recommendations(_headers_tuple, video_id):
    """获取教学建议（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/optimization/{video_id}/recommendations",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_highlights(_headers_tuple, video_id):
    """获取精彩片段（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/optimization/{video_id}/highlights",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_comparison(_headers_tuple):
    """获取跨课次对比数据（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/optimization/comparison",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


# 获取视频列表（使用缓存）
headers_tuple = tuple(sorted(get_api_headers().items()))
videos = fetch_video_list(headers_tuple)

# 侧边栏
with st.sidebar:
    st.markdown("### 🔍 筛选条件")
    
    if videos:
        video_options = {v['video_id']: f"{v.get('lesson_date', 'N/A')} {v.get('course_name', '-')} ({v.get('class_name', '-')})" for v in videos}
        
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
            options=list(video_options.keys()),
            format_func=lambda x: video_options[x],
            index=default_idx
        )
        st.caption("选择不同的课堂记录以查看详细分析。")
    else:
        st.warning("暂无已完成分析的视频")
        st.caption("请先上传并分析视频")
        selected_video_id = None

# 获取数据（使用缓存）
recommendations_data = fetch_recommendations(headers_tuple, selected_video_id) if selected_video_id else None
highlights_data = fetch_highlights(headers_tuple, selected_video_id) if selected_video_id else None
comparison_data = fetch_comparison(headers_tuple)

# ========== 页面标题 ==========
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
                if priority == 'high':
                    color = "#EF4444"
                    bg_color = "#FEF2F2"
                    border_color = "#FCA5A5"
                    icon = "🔴"
                elif priority == 'medium':
                    color = "#F59E0B"
                    bg_color = "#FFFBEB"
                    border_color = "#FCD34D"
                    icon = "🟡"
                else:
                    color = "#10B981"
                    bg_color = "#ECFDF5"
                    border_color = "#6EE7B7"
                    icon = "🟢"
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-left: 4px solid {color}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #111827; font-weight: 600; font-size: 1.1rem;">{icon} {rec.get('title', '建议')}</h4>
                        <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">{priority}</span>
                    </div>
                    <p style="color: #4B5563; margin-bottom: 16px; line-height: 1.6;">{rec.get('description', '')}</p>
                    <div style="background-color: white; padding: 16px; border-radius: 8px; border: 1px solid {border_color};">
                        <div style="font-weight: 600; color: {color}; margin-bottom: 10px; font-size: 0.9rem; display: flex; align-items: center;">
                            <span style="margin-right: 6px;">🚀</span> 建议行动
                        </div>
                        <ul style="margin: 0; padding-left: 20px; color: #4B5563; font-size: 0.95rem; line-height: 1.8;">
                            {''.join([f'<li style="margin-bottom: 6px;">{action}</li>' for action in rec.get('suggested_actions', [])])}
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
                if priority == 'high':
                    color = "#EF4444"
                    bg_color = "#FEF2F2"
                    border_color = "#FCA5A5"
                    icon = "🔴"
                elif priority == 'medium':
                    color = "#F59E0B"
                    bg_color = "#FFFBEB"
                    border_color = "#FCD34D"
                    icon = "🟡"
                else:
                    color = "#10B981"
                    bg_color = "#ECFDF5"
                    border_color = "#6EE7B7"
                    icon = "🟢"
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; border-left: 4px solid {color}; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #111827; font-weight: 600; font-size: 1.1rem;">{icon} {rec['title']}</h4>
                        <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">{priority}</span>
                    </div>
                    <p style="color: #4B5563; margin-bottom: 16px; line-height: 1.6;">{rec['description']}</p>
                    <div style="background-color: white; padding: 16px; border-radius: 8px; border: 1px solid {border_color};">
                        <div style="font-weight: 600; color: {color}; margin-bottom: 10px; font-size: 0.9rem; display: flex; align-items: center;">
                            <span style="margin-right: 6px;">🚀</span> 建议行动
                        </div>
                        <ul style="margin: 0; padding-left: 20px; color: #4B5563; font-size: 0.95rem; line-height: 1.8;">
                            {''.join([f'<li style="margin-bottom: 6px;">{action}</li>' for action in rec['suggested_actions']])}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎬 精彩片段回顾")
        
        if highlights_data and highlights_data.get('highlights'):
            for highlight in highlights_data['highlights']:
                start = highlight.get('start_time', 0) // 60
                end = highlight.get('end_time', 0) // 60
                score = highlight.get('score', 'N/A')
                
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);">
                    <div style="display: flex; gap: 16px;">
                        <div style="flex: 0 0 120px;">
                            <div style="width: 120px; height: 80px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;">
                                {start}m-{end}m
                            </div>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 1.2rem;">⭐</span>
                                <span style="font-weight: 600; color: #111827;">评分: {score}</span>
                                <span style="color: #6B7280; font-size: 0.9rem;">时段: {start}m - {end}m</span>
                            </div>
                            <p style="color: #4B5563; margin: 0 0 8px 0; line-height: 1.6;">{highlight.get('description', '')}</p>
                            {f'<div style="background-color: #EEF2FF; padding: 8px 12px; border-radius: 6px; margin-top: 8px;"><span style="color: #4338CA; font-size: 0.85rem; font-weight: 500;">💡 入选理由: </span><span style="color: #4B5563; font-size: 0.85rem;">{"、".join(highlight.get("reasons", []))}</span></div>' if highlight.get('reasons') else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
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
        
        # 雷达图容器
        with st.container():
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=current_values,
                theta=categories,
                fill='toself',
                name='本节课',
                line_color='#4F46E5',
                fillcolor='rgba(79, 70, 229, 0.2)'
            ))
            fig.add_trace(go.Scatterpolar(
                r=average_values,
                theta=categories,
                fill='toself',
                name='历史平均',
                line_color='#9CA3AF',
                line_dash='dot',
                fillcolor='rgba(156, 163, 175, 0.1)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5],
                        gridcolor="#E5E7EB",
                        showline=True,
                        linecolor="#D1D5DB"
                    ),
                    angularaxis=dict(
                        gridcolor="#E5E7EB",
                        linecolor="#D1D5DB"
                    ),
                    bgcolor="rgba(0,0,0,0)"
                ),
                showlegend=True,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=12)
                ),
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📈 历史趋势")
        
        if comparison_data and comparison_data.get('history'):
            dates = [h.get('date', '') for h in comparison_data['history']]
            scores = [h.get('score', 0) for h in comparison_data['history']]
        else:
            dates = ['10-01', '10-08', '10-15', '10-22', '10-29']
            scores = [7.5, 7.8, 8.2, 8.0, 8.5]
        
        fig2 = px.line(
            x=dates,
            y=scores,
            markers=True,
            title="教学质量评分趋势",
            labels={'x': '日期', 'y': '评分'}
        )
        fig2.update_traces(
            line=dict(color='#4F46E5', width=3),
            marker=dict(size=8, color='#4F46E5')
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis_range=[0, 10],
            xaxis=dict(gridcolor="#E5E7EB", showline=True, linecolor="#D1D5DB"),
            yaxis=dict(gridcolor="#E5E7EB", showline=True, linecolor="#D1D5DB"),
            title_font=dict(size=16, color='#111827'),
            font=dict(color='#4B5563')
        )
        st.plotly_chart(fig2, use_container_width=True)

# ==================== Tab 2: AI 教学顾问 ====================
with tab2:
    # 检查是否选择了视频
    if not selected_video_id:
        st.warning("👆 请先在侧边栏选择要分析的课堂视频")
        st.stop()
    
    # 获取当前视频信息
    current_video_info = next((v for v in videos if v.get('video_id') == selected_video_id), {})
    video_label = f"{current_video_info.get('lesson_date', 'N/A')} {current_video_info.get('course_name', '-')} ({current_video_info.get('class_name', '-')})"
    
    # AI 顾问介绍卡片
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="font-size: 2rem;">🤖</span>
            <h4 style="color: white; margin: 0; font-weight: 600;">AI 教学顾问</h4>
        </div>
        <p style="color: rgba(255, 255, 255, 0.9); margin: 0 0 16px 0; line-height: 1.6;">我是基于通义千问大模型的教学助手，专门分析课堂行为数据并提供教学改进建议。</p>
        <div style="background-color: rgba(255, 255, 255, 0.2); backdrop-filter: blur(10px); padding: 12px 16px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.3);">
            <span style="color: white; font-weight: 600; font-size: 0.9rem;">📹 当前分析：</span>
            <span style="color: white; font-size: 0.95rem; margin-left: 8px;">{video_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 为每个视频维护独立的聊天历史
    chat_key = f"chat_messages_{selected_video_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": f"您好！我已阅读 **{video_label}** 的行为分析数据。\n\n您可以问我：\n- 📊 这节课的整体表现如何？\n- 👀 学生的专注度怎么样？\n- 📈 互动情况分析\n- 💡 有什么需要改进的地方？"}
        ]

    # 聊天消息容器
    st.markdown("""
    <style>
    .chat-container {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        max-height: 500px;
        overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 显示历史消息
    with st.container():
        for message in st.session_state[chat_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 输入框和操作按钮
    col_input, col_clear = st.columns([5, 1])
    
    with col_input:
        prompt = st.chat_input("请输入您的问题（例如：如何提高后半段的学生专注度？）")
    
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ 清空", key="clear_chat", use_container_width=True):
            st.session_state[chat_key] = [
                {"role": "assistant", "content": "对话已清空。请问有什么可以帮您的？"}
            ]
            st.rerun()
    
    if prompt:
        # 用户消息
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # 显示加载状态，避免白屏
            message_placeholder.markdown("🤔 AI 正在分析数据并思考教学策略...")
            
            try:
                # 调用后端 Agent API
                response = requests.post(
                    f"{API_BASE_URL}/agent/chat",
                    headers=get_api_headers(),
                    json={
                        "video_id": selected_video_id,
                        "messages": st.session_state[chat_key]
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    full_response = result.get("content", "抱歉，未能获取回复。")
                else:
                    try:
                        error_detail = response.json().get("detail", "未知错误")
                    except:
                        error_detail = f"HTTP {response.status_code}"
                    full_response = f"⚠️ AI 服务暂时不可用：{error_detail}"
                    
            except requests.exceptions.Timeout:
                full_response = "⚠️ 请求超时，AI 正在处理大量数据，请稍后重试。"
            except requests.exceptions.ConnectionError:
                full_response = "⚠️ 无法连接到后端服务，请确认服务已启动。"
            except Exception as e:
                full_response = f"⚠️ 发生错误：{str(e)}"
            
            # 直接显示完整响应，移除阻塞式sleep
            message_placeholder.markdown(full_response)
        
        st.session_state[chat_key].append({"role": "assistant", "content": full_response})
        st.rerun()