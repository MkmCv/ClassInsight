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
    
    if timeline_data and timeline_data.get('timeline'):
        timeline_list = timeline_data['timeline']
        
        # 构建 DataFrame
        rows = []
        for item in timeline_list:
            ts = item.get('timestamp', 0)
            behaviors = item.get('behaviors', {})
            if behaviors:
                row = {"时间(秒)": ts, "时间(分钟)": round(ts / 60, 1)}
                row.update(behaviors)
                rows.append(row)
        
        if rows:
            df_timeline = pd.DataFrame(rows)
            
            # ==================== 1. 教学模式分析 ====================
            st.markdown("### 📚 教学模式时间线")
            st.caption("基于检测数据推断的教学活动类型")
            
            # 计算每个时间窗口的教学模式
            def get_teaching_mode(row):
                # 互动模式：有引导、回答或上台互动
                interaction = row.get('guide', 0) + row.get('answer', 0) + row.get('On-stage interaction', 0)
                # 板书模式：有板书行为
                blackboard = row.get('blackboard-writing', 0)
                # 多媒体模式：屏幕活跃
                multimedia = row.get('screen', 0)
                # 讲授模式：教师站立
                lecture = row.get('teacher', 0) + row.get('stand', 0)
                
                if interaction > 0:
                    return "🗣️ 互动教学"
                elif blackboard > 0:
                    return "✏️ 板书讲解"
                elif multimedia > 0:
                    return "🖥️ 多媒体演示"
                elif lecture > 0:
                    return "👨‍🏫 讲授模式"
                else:
                    return "⏸️ 其他"
            
            df_timeline['教学模式'] = df_timeline.apply(get_teaching_mode, axis=1)
            
            # 创建教学模式时间线（甘特图风格）
            mode_colors = {
                "🗣️ 互动教学": "#10B981",    # 绿色 - 最佳
                "✏️ 板书讲解": "#3B82F6",    # 蓝色
                "🖥️ 多媒体演示": "#8B5CF6",  # 紫色
                "👨‍🏫 讲授模式": "#F59E0B",    # 橙色
                "⏸️ 其他": "#9CA3AF"         # 灰色
            }
            
            fig_mode = px.scatter(
                df_timeline, 
                x="时间(分钟)", 
                y="教学模式",
                color="教学模式",
                color_discrete_map=mode_colors,
                size_max=15
            )
            fig_mode.update_traces(marker=dict(size=12, symbol='square'))
            fig_mode.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="时间（分钟）",
                yaxis_title="",
                showlegend=True,
                height=250
            )
            st.plotly_chart(fig_mode, use_container_width=True)
            
            # 教学模式占比统计
            mode_counts = df_timeline['教学模式'].value_counts()
            col_mode1, col_mode2 = st.columns([1, 2])
            with col_mode1:
                st.markdown("**模式占比**")
                for mode, count in mode_counts.items():
                    pct = count / len(df_timeline) * 100
                    st.write(f"{mode}: {pct:.1f}%")
            with col_mode2:
                fig_mode_pie = px.pie(
                    values=mode_counts.values, 
                    names=mode_counts.index,
                    color=mode_counts.index,
                    color_discrete_map=mode_colors,
                    hole=0.4
                )
                fig_mode_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    height=200,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_mode_pie, use_container_width=True)
            
            st.markdown("---")
            
            # ==================== 2. 互动强度曲线 ====================
            st.markdown("### 📈 课堂互动强度")
            st.caption("基于引导、回答、上台互动行为计算的互动指数")
            
            # 计算互动强度（0-100）
            def calc_interaction_score(row):
                guide = row.get('guide', 0) * 30       # 引导权重高
                answer = row.get('answer', 0) * 25     # 回答权重
                onstage = row.get('On-stage interaction', 0) * 45  # 上台互动权重最高
                score = min(100, guide + answer + onstage)
                return score
            
            df_timeline['互动指数'] = df_timeline.apply(calc_interaction_score, axis=1)
            
            # 计算教学丰富度（使用了多少种教学方式）
            def calc_richness(row):
                methods = 0
                if row.get('teacher', 0) > 0 or row.get('stand', 0) > 0: methods += 1
                if row.get('blackboard-writing', 0) > 0: methods += 1
                if row.get('screen', 0) > 0: methods += 1
                if row.get('guide', 0) > 0 or row.get('answer', 0) > 0: methods += 1
                return methods * 25  # 最高100
            
            df_timeline['教学丰富度'] = df_timeline.apply(calc_richness, axis=1)
            
            fig_interaction = go.Figure()
            
            # 互动指数曲线
            fig_interaction.add_trace(go.Scatter(
                x=df_timeline['时间(分钟)'],
                y=df_timeline['互动指数'],
                mode='lines+markers',
                name='互动指数',
                line=dict(color='#10B981', width=2),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.2)'
            ))
            
            # 教学丰富度曲线
            fig_interaction.add_trace(go.Scatter(
                x=df_timeline['时间(分钟)'],
                y=df_timeline['教学丰富度'],
                mode='lines',
                name='教学丰富度',
                line=dict(color='#8B5CF6', width=2, dash='dot')
            ))
            
            fig_interaction.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="时间（分钟）",
                yaxis_title="指数（0-100）",
                yaxis=dict(range=[0, 105]),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=300
            )
            st.plotly_chart(fig_interaction, use_container_width=True)
            
            # 关键指标卡片
            avg_interaction = df_timeline['互动指数'].mean()
            max_interaction = df_timeline['互动指数'].max()
            low_interaction_pct = (df_timeline['互动指数'] < 10).sum() / len(df_timeline) * 100
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("平均互动指数", f"{avg_interaction:.1f}", 
                         delta="良好" if avg_interaction > 30 else "需提升")
            with metric_col2:
                st.metric("峰值互动", f"{max_interaction:.0f}")
            with metric_col3:
                st.metric("低互动时段占比", f"{low_interaction_pct:.1f}%",
                         delta="正常" if low_interaction_pct < 50 else "偏高", delta_color="inverse")
            
            st.markdown("---")
            
            # ==================== 3. 教学行为热力图（真正的热力图）====================
            st.markdown("### 🔥 教学行为热力图")
            st.caption("颜色越深表示该时段该行为出现频率越高")
            
            # 选择要显示的行为
            behavior_cols = [col for col in df_timeline.columns 
                           if col not in ['时间(秒)', '时间(分钟)', '教学模式', '互动指数', '教学丰富度']]
            
            if behavior_cols:
                # 构建热力图数据
                heatmap_data = df_timeline[behavior_cols].T
                heatmap_data.columns = [f"{int(t//60)}:{int(t%60):02d}" for t in df_timeline['时间(秒)']]
                
                # 每隔几列取一个标签，避免太密
                step = max(1, len(heatmap_data.columns) // 15)
                x_labels = [heatmap_data.columns[i] if i % step == 0 else "" 
                           for i in range(len(heatmap_data.columns))]
                
                fig_heatmap = px.imshow(
                    heatmap_data.values,
                    x=list(range(len(heatmap_data.columns))),
                    y=heatmap_data.index,
                    color_continuous_scale='YlOrRd',
                    aspect='auto'
                )
                fig_heatmap.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="时间",
                    yaxis_title="行为类别",
                    xaxis=dict(
                        tickmode='array',
                        tickvals=list(range(0, len(x_labels), step)),
                        ticktext=[x_labels[i] for i in range(0, len(x_labels), step)]
                    ),
                    height=350
                )
                fig_heatmap.update_coloraxes(colorbar_title="检测次数")
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # ==================== 4. 原始数据折线图（可折叠）====================
            with st.expander("📊 查看原始检测数据"):
                selected = st.multiselect(
                    "选择展示的行为类别", 
                    behavior_cols, 
                    default=behavior_cols[:min(4, len(behavior_cols))]
                )
                if selected:
                    fig_raw = px.line(
                        df_timeline, x="时间(分钟)", y=selected, markers=True,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    fig_raw.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="时间（分钟）",
                        yaxis_title="检测数量",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_raw, use_container_width=True)
        else:
            st.warning("⚠️ 时间线数据为空")
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
