import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys
import os

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css

st.set_page_config(page_title="行为分析 - ClassInsight", page_icon="📈", layout="wide")

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


def fetch_behavior_summary(video_id):
    """获取行为汇总数据"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/summary",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


def fetch_behavior_timeline(video_id):
    """获取行为时间线数据"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/timeline",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def fetch_anomalies(video_id):
    """获取异常检测数据"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/anomalies",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def fetch_causation(video_id):
    """获取归因分析数据"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/causation",
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

if selected_video_id is None:
    st.markdown("# 📈 课堂行为分析报告")
    st.info("👆 请在侧边栏选择已分析的视频，或先上传新视频进行分析。")
    
    if st.button("前往上传视频", type="primary"):
        st.switch_page("pages/2_📤_视频上传.py")
    
    st.stop()

# 获取数据
summary_data = fetch_behavior_summary(selected_video_id)
timeline_data = fetch_behavior_timeline(selected_video_id)
anomalies_data = fetch_anomalies(selected_video_id)
causation_data = fetch_causation(selected_video_id)

# 获取视频信息
video_info = next((v for v in videos if v['video_id'] == selected_video_id), {})
video_label = f"{video_info.get('lesson_date', 'N/A')} {video_info.get('course_name', '-')} ({video_info.get('class_name', '-')})"

st.markdown(f"# 📈 课堂行为分析报告")
st.caption(f"分析对象: {video_label}")

# 检查数据是否可用
if summary_data is None:
    st.warning("⏳ 该视频分析数据暂不可用，可能仍在处理中。")
    st.stop()

# Tab 布局
tab1, tab2, tab3 = st.tabs(["📊 整课概览", "📉 时间趋势", "⚠️ 异常诊断"])

# ==================== Tab 1 ====================
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 从 summary 提取数据
    behavior_summary = summary_data.get('behavior_summary', {})
    teacher_behavior = summary_data.get('teacher_behavior', {})
    metrics = summary_data.get('metrics', {})
    
    # 关键指标
    c1, c2, c3, c4 = st.columns(4)
    
    discuss_data = behavior_summary.get('discuss', {'total_duration': 0, 'count': 0, 'percentage': 0})
    handraising_data = behavior_summary.get('hand-raising', {'total_duration': 0, 'count': 0, 'percentage': 0})
    bowhead_data = behavior_summary.get('BowHead', {'total_duration': 0, 'count': 0, 'percentage': 0})
    
    with c1:
        st.metric("互动总时长", f"{discuss_data.get('total_duration', 0)}s", "正常")
    with c2:
        st.metric("举手次数", f"{handraising_data.get('count', 0)}次", "")
    with c3:
        attention_rate = metrics.get('attention_rate', 0.85)
        st.metric("平均专注度", f"{attention_rate*100:.0f}%", "")
    with c4:
        bowhead_pct = bowhead_data.get('percentage', 0)
        delta_color = "inverse" if bowhead_pct > 15 else "normal"
        st.metric("低头率", f"{bowhead_pct:.1f}%", "偏高" if bowhead_pct > 15 else "正常", delta_color=delta_color)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 学生行为分布")
        
        # 过滤学生行为
        student_behavior_keys = ['discuss', 'hand-raising', 'read', 'write', 'BowHead', 'TurnHead', 'stand', 'answer', 'On-stage interaction']
        student_behaviors = {k: v for k, v in behavior_summary.items() if k in student_behavior_keys}
        
        if student_behaviors:
            df_student = pd.DataFrame([
                {"行为": k, "时长": v.get("total_duration", 0)} 
                for k, v in student_behaviors.items()
                if v.get("total_duration", 0) > 0
            ])
            
            if not df_student.empty:
                fig = px.pie(df_student, values='时长', names='行为', hole=0.6, 
                            color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无学生行为数据")
        else:
            st.info("暂无学生行为数据")
        
    with col2:
        st.markdown("### 教师行为分布")
        
        # 过滤教师行为
        teacher_behavior_keys = ['teacher', 'guide', 'blackboard-writing']
        teacher_behaviors = {k: v for k, v in behavior_summary.items() if k in teacher_behavior_keys}
        
        # 也可以从 teacher_behavior 字段获取
        if teacher_behavior:
            teacher_behaviors = teacher_behavior
        
        if teacher_behaviors:
            df_teacher = pd.DataFrame([
                {"行为": k, "时长": v.get("duration", v.get("total_duration", 0))} 
                for k, v in teacher_behaviors.items()
                if v.get("duration", v.get("total_duration", 0)) > 0
            ])
            
            if not df_teacher.empty:
                fig2 = px.pie(df_teacher, values='时长', names='行为', hole=0.6, 
                             color_discrete_sequence=px.colors.qualitative.Set3)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("暂无教师行为数据")
        else:
            st.info("暂无教师行为数据")

# ==================== Tab 2 ====================
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 课堂状态演变趋势")
    
    if timeline_data and timeline_data.get('timeline'):
        timeline_list = timeline_data['timeline']
        
        # 构建 DataFrame，将秒转换为 "分:秒" 格式
        rows = []
        for item in timeline_list:
            ts = item.get('timestamp', 0)
            behaviors = item.get('behaviors', {})
            if behaviors:  # 只添加有数据的点
                row = {"时间(秒)": ts, "时间(分)": round(ts / 60, 2)}
                row.update(behaviors)
                rows.append(row)
        
        if rows:
            df_timeline = pd.DataFrame(rows)
            
            # 显示数据统计
            st.caption(f"📊 共 {len(rows)} 个时间点，时间窗口: {timeline_data.get('window_size', 10)}秒")
            
            all_behaviors = [col for col in df_timeline.columns if col not in ["时间(秒)", "时间(分)"]]
            
            if all_behaviors:
                # 设置默认选中的行为
                default_behaviors = [b for b in ['guide', 'teacher', 'stand', 'screen', 'blackBoard'] if b in all_behaviors]
                if not default_behaviors:
                    default_behaviors = all_behaviors[:min(3, len(all_behaviors))]
                
                selected = st.multiselect("选择展示行为", all_behaviors, default=default_behaviors)
                
                if selected:
                    # 使用秒数作为 x 轴，更准确
                    fig_line = px.line(df_timeline, x="时间(秒)", y=selected, markers=True, 
                                       color_discrete_sequence=px.colors.qualitative.Bold)
                    fig_line.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        hovermode="x unified",
                        xaxis_title="时间（秒）",
                        yaxis_title="检测数量"
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                    
                    st.markdown("### 课堂注意力热力图")
                    fig_area = px.area(df_timeline, x="时间(秒)", y=all_behaviors, 
                                       color_discrete_sequence=px.colors.qualitative.Safe)
                    fig_area.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="时间（秒）",
                        yaxis_title="检测数量"
                    )
                    st.plotly_chart(fig_area, use_container_width=True)
                else:
                    st.info("请选择至少一个行为进行展示")
            else:
                st.warning("⚠️ 时间线数据中没有检测到任何行为")
        else:
            st.warning("⚠️ 时间线数据为空，可能视频中没有检测到目标行为")
    else:
        st.info("暂无时间线数据，请等待视频分析完成。")

# ==================== Tab 3 ====================
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### ⚠️ 异常事件列表")
        
        if anomalies_data and anomalies_data.get('anomalies'):
            for anomaly in anomalies_data['anomalies']:
                start = anomaly.get('start_time', 0) // 60
                end = anomaly.get('end_time', 0) // 60
                severity = anomaly.get('severity', 'medium')
                
                color = "#EF4444" if severity == "high" else "#F59E0B" if severity == "medium" else "#3B82F6"
                
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding-left: 12px; margin-bottom: 16px; background-color: #FFFFFF; padding: 16px; border-radius: 0 8px 8px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <div style="font-weight: 600; font-size: 1.1rem; color: #111827;">{anomaly.get('description', '未知异常')}</div>
                    <div style="color: #6B7280; font-size: 0.9rem; margin-top: 4px;">
                        <span style="background-color: {color}20; color: {color}; padding: 2px 8px; border-radius: 4px; font-weight: 500;">{severity.upper()}</span>
                        &nbsp; • &nbsp; {start}分 - {end}分
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ 未检测到明显异常，课堂状态良好！")
            
    with col_right:
        st.markdown("### 🔗 归因分析")
        
        if causation_data:
            correlations = causation_data.get('correlations', [])
            if correlations:
                # 显示最强相关性
                top_corr = correlations[0] if correlations else None
                if top_corr:
                    # 后端返回 student_behavior, teacher_behavior, correlation_coefficient
                    b1 = top_corr.get('teacher_behavior', top_corr.get('behavior1', '-'))
                    b2 = top_corr.get('student_behavior', top_corr.get('behavior2', '-'))
                    corr_val = top_corr.get('correlation_coefficient', top_corr.get('correlation', 0))
                    st.info(f'💡 **AI 洞察**：分析发现，教师的「{b1}」行为与学生的「{b2}」行为存在显著相关 (Corr: {corr_val:.2f})。')
            
            # 构建相关性矩阵
            if correlations:
                behaviors = list(set(
                    [c.get('teacher_behavior', c.get('behavior1', '')) for c in correlations] + 
                    [c.get('student_behavior', c.get('behavior2', '')) for c in correlations]
                ))
                behaviors = [b for b in behaviors if b]  # 过滤空值
                
                if behaviors:
                    corr_matrix = pd.DataFrame(1.0, index=behaviors, columns=behaviors)
                    
                    for c in correlations:
                        b1 = c.get('teacher_behavior', c.get('behavior1'))
                        b2 = c.get('student_behavior', c.get('behavior2'))
                        corr_val = c.get('correlation_coefficient', c.get('correlation', 0))
                        if b1 in behaviors and b2 in behaviors:
                            corr_matrix.loc[b1, b2] = corr_val
                            corr_matrix.loc[b2, b1] = corr_val
                    
                    fig_corr = px.imshow(corr_matrix, text_auto='.2f', color_continuous_scale='RdBu_r', aspect="auto")
                    fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_corr, use_container_width=True)
        else:
            # 默认显示示例
            st.info("💡 **AI 洞察**：数据收集中，完成更多课程分析后将展示行为关联性。")
            
            mock_corr = pd.DataFrame(
                [[1.0, 0.75, -0.2], [0.75, 1.0, -0.1], [-0.2, -0.1, 1.0]],
                columns=['引导', '讨论', '低头'],
                index=['引导', '讨论', '低头']
            )
            fig_corr = px.imshow(mock_corr, text_auto=True, color_continuous_scale='RdBu_r', aspect="auto")
            fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_corr, use_container_width=True)
