import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import sys
import os

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar

st.set_page_config(page_title="行为分析 - ClassInsight", page_icon="📈", layout="wide")

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
def fetch_behavior_summary(_headers_tuple, video_id):
    """获取行为汇总数据（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/summary",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_behavior_timeline(_headers_tuple, video_id):
    """获取行为时间线数据（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/timeline",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_anomalies(_headers_tuple, video_id):
    """获取异常检测数据（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/anomalies",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_causation(_headers_tuple, video_id):
    """获取归因分析数据（真实相关性分析，缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/causation",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def fetch_teaching_modes(_headers_tuple, video_id):
    """获取教学模式分析数据（缓存60秒）"""
    try:
        headers = dict(_headers_tuple)
        response = requests.get(
            f"{API_BASE_URL}/analysis/{video_id}/teaching-modes",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 404:
            # 视频不存在或分析未完成
            return None
        else:
            # 其他错误
            return None
    except requests.exceptions.RequestException as e:
        # 网络错误
        return None
    except Exception as e:
        # 其他异常
        return None


# 获取视频列表（使用缓存）
headers_tuple = tuple(sorted(get_api_headers().items()))
videos = fetch_video_list(headers_tuple)

# 侧边栏
with st.sidebar:
    st.markdown("### 🔍 筛选条件")
    
    if videos:
        # 提取所有可用的筛选选项
        all_courses = sorted(set([v.get('course_name', '') for v in videos if v.get('course_name')]))
        all_classes = sorted(set([v.get('class_name', '') for v in videos if v.get('class_name')]))
        all_dates = sorted(set([v.get('lesson_date', '') for v in videos if v.get('lesson_date')]), reverse=True)
        
        # 筛选条件
        st.markdown("#### 📅 按日期筛选")
        selected_date = st.selectbox(
            "选择日期",
            options=["全部"] + all_dates,
            key="filter_date",
            help="选择特定日期查看该日期的视频"
        )
        
        st.markdown("#### 📚 按课程筛选")
        selected_course = st.selectbox(
            "选择课程",
            options=["全部"] + all_courses,
            key="filter_course",
            help="选择特定课程查看该课程的视频"
        )
        
        st.markdown("#### 🏫 按班级筛选")
        selected_class = st.selectbox(
            "选择班级",
            options=["全部"] + all_classes,
            key="filter_class",
            help="选择特定班级查看该班级的视频"
        )
        
        # 应用筛选条件
        filtered_videos = videos
        if selected_date != "全部":
            filtered_videos = [v for v in filtered_videos if v.get('lesson_date') == selected_date]
        if selected_course != "全部":
            filtered_videos = [v for v in filtered_videos if v.get('course_name') == selected_course]
        if selected_class != "全部":
            filtered_videos = [v for v in filtered_videos if v.get('class_name') == selected_class]
        
        # 重置筛选按钮
        if selected_date != "全部" or selected_course != "全部" or selected_class != "全部":
            if st.button("🔄 重置筛选", key="reset_filters", use_container_width=True):
                st.session_state['filter_date'] = "全部"
                st.session_state['filter_course'] = "全部"
                st.session_state['filter_class'] = "全部"
                st.rerun()
        
        st.markdown("---")
        
        # 视频选择
        st.markdown("#### 🎬 选择课堂记录")
        
        if filtered_videos:
            video_options = {v['video_id']: f"{v.get('lesson_date', 'N/A')} {v.get('course_name', '-')} ({v.get('class_name', '-')})" for v in filtered_videos}
            
            # 如果有当前视频ID，默认选中
            default_idx = 0
            if 'current_video_id' in st.session_state and st.session_state['current_video_id']:
                try:
                    video_ids = list(video_options.keys())
                    if st.session_state['current_video_id'] in video_ids:
                        default_idx = video_ids.index(st.session_state['current_video_id'])
                        # 显示提示信息
                        st.success(f"✅ 已选择视频 ID: {st.session_state['current_video_id']}")
                except:
                    pass
            
            selected_video_id = st.selectbox(
                "选择视频",
                options=list(video_options.keys()),
                format_func=lambda x: video_options[x],
                index=default_idx,
                key="video_selector"
            )
            
            # 更新 session_state 中的当前视频ID
            if selected_video_id:
                st.session_state['current_video_id'] = selected_video_id
            
            # 显示筛选结果统计
            if len(filtered_videos) < len(videos):
                st.caption(f"📊 筛选结果: {len(filtered_videos)}/{len(videos)} 个视频")
            else:
                st.caption("选择不同的课堂记录以查看详细分析。")
        else:
            st.warning("⚠️ 没有符合条件的视频")
            st.caption("请调整筛选条件或上传新视频")
            selected_video_id = None
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

# 获取数据（使用缓存，显示加载状态）
with st.spinner("📊 正在加载分析数据..."):
    summary_data = fetch_behavior_summary(headers_tuple, selected_video_id)
    timeline_data = fetch_behavior_timeline(headers_tuple, selected_video_id)
    anomalies_data = fetch_anomalies(headers_tuple, selected_video_id)
    causation_data = fetch_causation(headers_tuple, selected_video_id)
    teaching_modes_data = fetch_teaching_modes(headers_tuple, selected_video_id)

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
tab1, tab2, tab3, tab4 = st.tabs(["📊 整课概览", "📉 时间趋势", "⚠️ 异常诊断", "🎓 教学模式"])

# ==================== Tab 1 ====================
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 从 summary 提取数据
    behavior_summary = summary_data.get('behavior_summary', {})
    teacher_behavior = summary_data.get('teacher_behavior', {})
    metrics = summary_data.get('metrics', {})
    
    # 关键指标（兼容分类后的行为数据）
    c1, c2, c3, c4 = st.columns(4)
    
    # 兼容处理：优先使用分类后的数据，否则使用原始数据
    # 讨论/互动：分类后为"讨论"，原始为"discuss"
    discuss_data = behavior_summary.get('讨论', behavior_summary.get('discuss', {'total_duration': 0, 'count': 0, 'percentage': 0}))
    # 举手：分类后为"学生举手"，原始为"hand-raising"
    handraising_data = behavior_summary.get('学生举手', behavior_summary.get('hand-raising', {'total_duration': 0, 'count': 0, 'percentage': 0}))
    # 低头：原始为"BowHead"（分类后可能包含在"其它"中，暂时使用原始数据）
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
        
        # 使用分类后的学生行为数据（如果API返回的是分类后的数据，直接使用；否则使用原始数据）
        # 分类后的学生行为类别：读写、台上展示、学生板书、回答问题、朗读、讨论、听讲、学生举手、其它
        student_behavior_categories = ['读写', '台上展示', '学生板书', '回答问题', '朗读', '讨论', '听讲', '学生举手', '其它']
        
        # 检查是否有分类后的数据（中文类别名）
        student_behaviors = {}
        if any(k in student_behavior_categories for k in behavior_summary.keys()):
            # 使用分类后的数据
            student_behaviors = {k: v for k, v in behavior_summary.items() if k in student_behavior_categories}
        else:
            # 向后兼容：使用原始数据
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
        
        # 使用分类后的教师行为数据
        # 分类后的教师行为类别：讲授、指导、应答、台上互动、教师板书、巡视、其它
        teacher_behavior_categories = ['讲授', '指导', '应答', '台上互动', '教师板书', '巡视', '其它']
        
        # 优先使用 teacher_behavior 字段（如果存在）
        if teacher_behavior:
            teacher_behaviors = teacher_behavior
        else:
            # 检查是否有分类后的数据（中文类别名）
            if any(k in teacher_behavior_categories for k in behavior_summary.keys()):
                # 使用分类后的数据
                teacher_behaviors = {k: v for k, v in behavior_summary.items() if k in teacher_behavior_categories}
            else:
                # 向后兼容：使用原始数据
                teacher_behavior_keys = ['teacher', 'guide', 'blackboard-writing', 'answer', 'On-stage interaction']
                teacher_behaviors = {k: v for k, v in behavior_summary.items() if k in teacher_behavior_keys}
        
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
            
            # 计算每个时间窗口的教学模式（兼容分类后的行为数据）
            def get_teaching_mode(row):
                # 兼容处理：检查是否有分类后的行为数据
                # 互动模式：分类后为"指导"、"应答"、"台上互动"，原始为"guide"、"answer"、"On-stage interaction"
                interaction = (
                    row.get('指导', 0) + row.get('应答', 0) + row.get('台上互动', 0) +  # 分类后的数据
                    row.get('guide', 0) + row.get('answer', 0) + row.get('On-stage interaction', 0)  # 原始数据
                )
                # 板书模式：分类后为"教师板书"，原始为"blackboard-writing"
                blackboard = row.get('教师板书', 0) + row.get('blackboard-writing', 0)
                # 多媒体模式：屏幕活跃（暂时没有分类后的对应）
                multimedia = row.get('screen', 0)
                # 讲授模式：分类后为"讲授"，原始为"teacher"+"stand"
                lecture = row.get('讲授', 0) + row.get('teacher', 0) + row.get('stand', 0)
                
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
            
            # 计算互动强度（0-100，兼容分类后的行为数据）
            def calc_interaction_score(row):
                # 兼容处理：分类后的"指导"、"应答"、"台上互动"
                guide = (row.get('指导', 0) + row.get('guide', 0)) * 30       # 引导权重高
                answer = (row.get('应答', 0) + row.get('answer', 0)) * 25     # 回答权重
                onstage = (row.get('台上互动', 0) + row.get('On-stage interaction', 0)) * 45  # 上台互动权重最高
                score = min(100, guide + answer + onstage)
                return score
            
            df_timeline['互动指数'] = df_timeline.apply(calc_interaction_score, axis=1)
            
            # 计算教学丰富度（使用了多少种教学方式，兼容分类后的行为数据）
            def calc_richness(row):
                methods = 0
                # 讲授模式：分类后为"讲授"，原始为"teacher"+"stand"
                if row.get('讲授', 0) > 0 or row.get('teacher', 0) > 0 or row.get('stand', 0) > 0: 
                    methods += 1
                # 板书：分类后为"教师板书"，原始为"blackboard-writing"
                if row.get('教师板书', 0) > 0 or row.get('blackboard-writing', 0) > 0: 
                    methods += 1
                # 多媒体：暂时没有分类后的对应
                if row.get('screen', 0) > 0: 
                    methods += 1
                # 互动：分类后为"指导"、"应答"，原始为"guide"、"answer"
                if (row.get('指导', 0) > 0 or row.get('应答', 0) > 0 or 
                    row.get('guide', 0) > 0 or row.get('answer', 0) > 0): 
                    methods += 1
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
        st.markdown("### 🔗 真实相关性分析")
        st.caption("基于皮尔逊相关系数计算，数据驱动")
        
        if causation_data:
            correlations = causation_data.get('correlations', [])
            if correlations:
                # 显示相关性列表
                st.markdown("**显著相关性（p < 0.05）**")
                for i, corr in enumerate(correlations[:5]):  # 显示前5个
                    teacher_b = corr.get('teacher_behavior', '')
                    student_b = corr.get('student_behavior', '')
                    corr_val = corr.get('correlation_coefficient', 0)
                    lag = corr.get('lag_time', 0)
                    interpretation = corr.get('interpretation', '')
                    
                    corr_color = "#10B981" if corr_val > 0 else "#EF4444"
                    lag_text = f" | 滞后: {lag}秒" if lag > 0 else ""
                    
                    # 使用单行HTML字符串，避免换行导致的渲染问题
                    html_content = f'<div style="padding: 12px; margin-bottom: 8px; background-color: #F9FAFB; border-radius: 6px; border-left: 3px solid {corr_color};"><div style="font-weight: 600; color: #111827; margin-bottom: 4px;">{teacher_b} ↔ {student_b}</div><div style="font-size: 0.85rem; color: #6B7280; margin-bottom: 2px;">相关系数: <strong>{corr_val:.3f}</strong>{lag_text}</div><div style="font-size: 0.8rem; color: #9CA3AF;">{interpretation}</div></div>'
                    st.markdown(html_content, unsafe_allow_html=True)
                
                # 构建相关性矩阵（仅显示有相关性的行为对）
                if len(correlations) > 0:
                    teacher_behaviors = list(set([c.get('teacher_behavior') for c in correlations]))
                    student_behaviors = list(set([c.get('student_behavior') for c in correlations]))
                    
                    if teacher_behaviors and student_behaviors:
                        # 创建矩阵
                        corr_matrix = pd.DataFrame(
                            0.0,
                            index=teacher_behaviors,
                            columns=student_behaviors
                        )
                        
                        for c in correlations:
                            t_b = c.get('teacher_behavior')
                            s_b = c.get('student_behavior')
                            corr_val = c.get('correlation_coefficient', 0)
                            if t_b in teacher_behaviors and s_b in student_behaviors:
                                corr_matrix.loc[t_b, s_b] = corr_val
                        
                        if not corr_matrix.empty:
                            st.markdown("**相关性矩阵**")
                            fig_corr = px.imshow(
                                corr_matrix,
                                text_auto='.2f',
                                color_continuous_scale='RdBu_r',
                                aspect="auto",
                                labels=dict(x="学生行为", y="教师行为", color="相关系数")
                            )
                            fig_corr.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                height=300
                            )
                            st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("💡 未发现显著相关性（p < 0.05 且 |r| > 0.3）")
        else:
            st.info("💡 数据收集中，请等待分析完成。")

# ==================== Tab 4 ====================
with tab4:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if teaching_modes_data:
        modes = teaching_modes_data.get('modes', [])
        mode_percentages = teaching_modes_data.get('mode_percentages', {})
        transitions = teaching_modes_data.get('transitions', [])
        mode_timeline = teaching_modes_data.get('mode_timeline', [])
        
        # 检查是否有数据（优先检查mode_percentages，因为它更可靠）
        if mode_percentages or modes or mode_timeline:
            st.markdown("### 🎓 教学模式识别")
            st.caption("基于行为数据自动识别的教学模式")
            
            # 模式分布
            col_mode1, col_mode2 = st.columns([1, 2])
            
            with col_mode1:
                st.markdown("**模式占比**")
                mode_colors = {
                    "互动教学": "#10B981",
                    "板书讲解": "#3B82F6",
                    "多媒体演示": "#8B5CF6",
                    "练习模式": "#F59E0B",
                    "讲授模式": "#EF4444",
                    "其他": "#9CA3AF"
                }
                
                if mode_percentages:
                    for mode, pct in sorted(mode_percentages.items(), key=lambda x: x[1], reverse=True):
                        color = mode_colors.get(mode, "#9CA3AF")
                        st.markdown(f"""
                        <div style="padding: 8px; margin-bottom: 6px; background-color: {color}20; border-radius: 4px; border-left: 3px solid {color};">
                            <span style="font-weight: 600;">{mode}</span>
                            <span style="float: right; color: #6B7280;">{pct:.1f}%</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("暂无模式占比数据")
            
            with col_mode2:
                # 模式占比饼图
                if mode_percentages:
                    fig_mode = px.pie(
                        values=list(mode_percentages.values()),
                        names=list(mode_percentages.keys()),
                        color=list(mode_percentages.keys()),
                        color_discrete_map=mode_colors,
                        hole=0.4
                    )
                    fig_mode.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=True,
                        height=300
                    )
                    st.plotly_chart(fig_mode, use_container_width=True)
            
            st.markdown("---")
            
            # 模式时间线
            if mode_timeline and len(mode_timeline) > 0:
                st.markdown("### 📈 教学模式时间线")
                
                try:
                    # 确保数据格式正确
                    timeline_list = []
                    for item in mode_timeline:
                        if isinstance(item, dict):
                            timeline_list.append({
                                'timestamp': item.get('timestamp', 0),
                                'mode': item.get('mode', '其他')
                            })
                        else:
                            # 如果是对象，尝试访问属性
                            timeline_list.append({
                                'timestamp': getattr(item, 'timestamp', 0),
                                'mode': getattr(item, 'mode', '其他')
                            })
                    
                    if timeline_list:
                        df_mode = pd.DataFrame(timeline_list)
                        df_mode['时间(分钟)'] = df_mode['timestamp'] / 60
                        
                        # 创建模式时间线图
                        fig_mode_timeline = px.scatter(
                            df_mode,
                            x='时间(分钟)',
                            y='mode',
                            color='mode',
                            color_discrete_map=mode_colors,
                            size_max=15
                        )
                        fig_mode_timeline.update_traces(marker=dict(size=12, symbol='square'))
                        fig_mode_timeline.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            xaxis_title="时间（分钟）",
                            yaxis_title="教学模式",
                            showlegend=True,
                            height=300
                        )
                        st.plotly_chart(fig_mode_timeline, use_container_width=True)
                    else:
                        st.info("模式时间线数据格式不正确")
                except Exception as e:
                    st.error(f"处理模式时间线时出错: {str(e)}")
                    st.info("请检查后端API返回的数据格式")
            
            st.markdown("---")
            
            # 模式转换分析
            if transitions:
                st.markdown("### 🔄 模式转换分析")
                
                # 转换频率统计
                transition_counts = {}
                for trans in transitions:
                    key = f"{trans.get('from_mode')} → {trans.get('to_mode')}"
                    transition_counts[key] = transition_counts.get(key, 0) + trans.get('count', 1)
                
                if transition_counts:
                    df_trans = pd.DataFrame([
                        {"转换": k, "次数": v}
                        for k, v in sorted(transition_counts.items(), key=lambda x: x[1], reverse=True)
                    ])
                    
                    fig_trans = px.bar(
                        df_trans,
                        x='转换',
                        y='次数',
                        color='次数',
                        color_continuous_scale='Blues'
                    )
                    fig_trans.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        xaxis_title="模式转换",
                        yaxis_title="转换次数",
                        height=300
                    )
                    st.plotly_chart(fig_trans, use_container_width=True)
                    
                    # 转换列表
                    st.markdown("**转换详情**")
                    for trans in sorted(transitions, key=lambda x: x.get('count', 0), reverse=True)[:10]:
                        st.write(f"- **{trans.get('from_mode')}** → **{trans.get('to_mode')}**: {trans.get('count')}次")
                else:
                    st.info("暂无模式转换数据")
            else:
                st.info("暂无模式转换数据")
        else:
            st.info("暂无教学模式数据，请确保视频分析已完成。")
    else:
        st.info("💡 教学模式分析数据暂不可用，请等待分析完成。")