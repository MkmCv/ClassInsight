import streamlit as st
import requests
import sys
import os
import time
from datetime import datetime, date, time as dt_time, timedelta

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar

st.set_page_config(page_title="课表管理 - ClassInsight", page_icon="📅", layout="wide")

load_css()

# ==================== 权限检查 ====================
if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

render_sidebar()

current_user = st.session_state.get('user', {})
if current_user.get('role') != 'admin':
    st.error("⚠️ 只有管理员可以访问此页面")
    st.stop()

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
USE_BACKEND_API = True


def get_api_headers():
    headers = {"Content-Type": "application/json"}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers


# ==================== 数据获取函数 ====================
@st.cache_data(ttl=30, show_spinner=False)
def get_teachers(_headers_tuple):
    """获取教师列表（缓存30秒）"""
    if not USE_BACKEND_API:
        return [
            {"id": 1, "username": "teacher001", "unit": "岭南师范学院", "class_name": "高一(1)班"},
            {"id": 2, "username": "teacher002", "unit": "岭南师范学院", "class_name": "高一(2)班"},
        ]
    try:
        headers = dict(_headers_tuple)
        response = requests.get(f"{API_BASE_URL}/schedules/teachers", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def get_all_schedules(_headers_tuple, teacher_id=None, day_of_week=None):
    """获取所有课表（缓存30秒）"""
    if not USE_BACKEND_API:
        return [
            {"id": 1, "user_id": 1, "teacher_name": "teacher001", "course_name": "数学(代数)", 
             "class_name": "高一(1)班", "day_of_week": 0, "start_time": "08:00:00", "end_time": "08:45:00"},
            {"id": 2, "user_id": 1, "teacher_name": "teacher001", "course_name": "数学(几何)", 
             "class_name": "高一(3)班", "day_of_week": 0, "start_time": "10:00:00", "end_time": "10:45:00"},
            {"id": 3, "user_id": 2, "teacher_name": "teacher002", "course_name": "数学(习题)", 
             "class_name": "高一(2)班", "day_of_week": 1, "start_time": "14:00:00", "end_time": "14:45:00"},
            {"id": 4, "user_id": 1, "teacher_name": "teacher001", "course_name": "高等数学", 
             "class_name": "高一(1)班", "day_of_week": 3, "start_time": "09:00:00", "end_time": "09:45:00"},
        ]
    try:
        headers = dict(_headers_tuple)
        params = {}
        if teacher_id:
            params["user_id"] = teacher_id
        if day_of_week is not None:
            params["day_of_week"] = day_of_week
        response = requests.get(f"{API_BASE_URL}/schedules/all", headers=headers, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []


def create_schedule(data):
    if not USE_BACKEND_API:
        return True, {"id": 999}
    try:
        response = requests.post(f"{API_BASE_URL}/schedules", headers=get_api_headers(), json=data, timeout=5)
        if response.status_code == 201:
            return True, response.json()
        return False, response.json().get("detail", "创建失败")
    except Exception as e:
        return False, str(e)


def update_schedule(schedule_id, data):
    if not USE_BACKEND_API:
        return True, "更新成功"
    try:
        response = requests.put(f"{API_BASE_URL}/schedules/{schedule_id}", headers=get_api_headers(), json=data, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, response.json().get("detail", "更新失败")
    except Exception as e:
        return False, str(e)


def delete_schedule(schedule_id):
    if not USE_BACKEND_API:
        return True, "删除成功"
    try:
        response = requests.delete(f"{API_BASE_URL}/schedules/{schedule_id}", headers=get_api_headers(), timeout=5)
        if response.status_code == 200:
            return True, "删除成功"
        return False, response.json().get("detail", "删除失败")
    except Exception as e:
        return False, str(e)


def get_week_dates(target_date):
    days_since_monday = target_date.weekday()
    monday = target_date - timedelta(days=days_since_monday)
    return [monday + timedelta(days=i) for i in range(7)]


# ==================== 页面布局 ====================
st.markdown("# 📅 课表管理")
st.markdown("为教师安排课程，管理周课表。")

DAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
DAY_NAMES_FULL = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

tab1, tab2, tab3 = st.tabs(["📅 日历视图", "📋 列表视图", "➕ 新增课程"])

# ==================== Tab1: 日历视图 ====================
with tab1:
    col_date, col_teacher, col_nav = st.columns([2, 2, 3])
    
    with col_date:
        selected_date = st.date_input("选择周", value=date.today(), key="calendar_week")
    
    # 获取教师列表（使用缓存）
    headers_tuple = tuple(sorted(get_api_headers().items()))
    teachers = get_teachers(headers_tuple)
    teacher_options = {0: "👥 全部教师"}
    teacher_options.update({t['id']: f"👨‍🏫 {t['username']}" for t in teachers})
    
    with col_teacher:
        calendar_teacher = st.selectbox("筛选教师", options=list(teacher_options.keys()),
                                        format_func=lambda x: teacher_options[x], key="calendar_teacher_filter")
    
    with col_nav:
        nav1, nav2, nav3 = st.columns(3)
        with nav1:
            if st.button("◀ 上周", key="prev_week", use_container_width=True):
                st.session_state['calendar_week'] = selected_date - timedelta(days=7)
                st.rerun()
        with nav2:
            if st.button("📍 本周", key="this_week", use_container_width=True):
                st.session_state['calendar_week'] = date.today()
                st.rerun()
        with nav3:
            if st.button("下周 ▶", key="next_week", use_container_width=True):
                st.session_state['calendar_week'] = selected_date + timedelta(days=7)
                st.rerun()
    
    week_dates = get_week_dates(selected_date)
    today = date.today()
    
    st.markdown(f"### 📆 {week_dates[0].strftime('%Y-%m-%d')} 至 {week_dates[6].strftime('%Y-%m-%d')}")
    
    filter_teacher = calendar_teacher if calendar_teacher > 0 else None
    schedules = get_all_schedules(headers_tuple, filter_teacher, None)
    
    # 注入CSS样式
    st.markdown("""
<style>
.schedule-grid {
    display: grid;
    grid-template-columns: 70px repeat(7, 1fr);
    gap: 4px;
    font-size: 0.85rem;
}
.schedule-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 10px 6px;
    border-radius: 8px;
    text-align: center;
    font-weight: 600;
}
.schedule-header.today {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}
.schedule-header.time-col {
    background: #374151;
}
.schedule-time {
    background: #f3f4f6;
    padding: 8px 4px;
    border-radius: 6px;
    text-align: center;
    color: #6b7280;
    font-weight: 500;
}
.schedule-cell {
    background: #fafafa;
    border-radius: 6px;
    min-height: 50px;
    padding: 4px;
}
.course-item {
    background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
    border-left: 3px solid #4f46e5;
    border-radius: 6px;
    padding: 6px 8px;
    margin-bottom: 4px;
}
.course-item .name {
    font-weight: 600;
    color: #312e81;
}
.course-item .info {
    color: #4338ca;
    font-size: 0.75rem;
}
.course-item.t2 {
    background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
    border-left-color: #db2777;
}
.course-item.t2 .name { color: #831843; }
.course-item.t2 .info { color: #9d174d; }
.course-item.t3 {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-left-color: #059669;
}
.course-item.t3 .name { color: #064e3b; }
.course-item.t3 .info { color: #047857; }
.course-item.t4 {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-left-color: #d97706;
}
.course-item.t4 .name { color: #78350f; }
.course-item.t4 .info { color: #92400e; }
.empty-cell {
    color: #d1d5db;
    text-align: center;
    padding: 15px 0;
}
</style>
    """, unsafe_allow_html=True)
    
    # 按时间段组织课程
    schedule_by_day_time = {}
    for s in schedules:
        day = s.get('day_of_week', 0)
        hour = int(s.get('start_time', '08:00:00')[:2])
        key = (day, hour)
        if key not in schedule_by_day_time:
            schedule_by_day_time[key] = []
        schedule_by_day_time[key].append(s)
    
    # 找出所有有课的时间段
    active_hours = sorted(set(k[1] for k in schedule_by_day_time.keys())) if schedule_by_day_time else [8, 9, 10, 14, 15]
    
    # 构建表头HTML
    header_html = '<div class="schedule-grid"><div class="schedule-header time-col">时间</div>'
    for i, d in enumerate(week_dates):
        today_class = " today" if d == today else ""
        header_html += f'<div class="schedule-header{today_class}">{DAY_NAMES[i]}<br><span style="font-size:0.8rem;opacity:0.9">{d.strftime("%m/%d")}</span></div>'
    header_html += '</div>'
    st.markdown(header_html, unsafe_allow_html=True)
    
    # 构建每个时间段的行
    for hour in active_hours:
        row_html = f'<div class="schedule-grid"><div class="schedule-time">{hour:02d}:00</div>'
        
        for day_idx in range(7):
            row_html += '<div class="schedule-cell">'
            key = (day_idx, hour)
            if key in schedule_by_day_time:
                for s in schedule_by_day_time[key]:
                    tid = s.get('user_id', 1)
                    t_class = f"t{(tid % 4) + 1}" if tid > 1 else ""
                    start = s.get('start_time', '')[:5]
                    end = s.get('end_time', '')[:5]
                    row_html += f'''<div class="course-item {t_class}">
                        <div class="name">{s.get('course_name', '')}</div>
                        <div class="info">📍 {s.get('class_name', '')}</div>
                        <div class="info">⏰ {start}-{end}</div>
                        <div class="info">👨‍🏫 {s.get('teacher_name', '')}</div>
                    </div>'''
            else:
                row_html += '<div class="empty-cell">—</div>'
            row_html += '</div>'
        
        row_html += '</div>'
        st.markdown(row_html, unsafe_allow_html=True)
    
    # 图例
    st.markdown("""
<div style="display:flex;gap:15px;justify-content:center;margin-top:15px;font-size:0.85rem;">
    <span>📌 <b>图例:</b></span>
    <span style="background:#e0e7ff;padding:4px 10px;border-radius:4px;border-left:3px solid #4f46e5;">教师1</span>
    <span style="background:#fce7f3;padding:4px 10px;border-radius:4px;border-left:3px solid #db2777;">教师2</span>
    <span style="background:#d1fae5;padding:4px 10px;border-radius:4px;border-left:3px solid #059669;">教师3</span>
    <span style="background:#fef3c7;padding:4px 10px;border-radius:4px;border-left:3px solid #d97706;">教师4</span>
</div>
    """, unsafe_allow_html=True)

# ==================== Tab2: 列表视图 ====================
with tab2:
    col_filter1, col_filter2, _ = st.columns([2, 2, 4])
    
    with col_filter1:
        list_teacher = st.selectbox("筛选教师", options=list(teacher_options.keys()),
                                    format_func=lambda x: teacher_options[x], key="list_teacher_filter")
    
    with col_filter2:
        day_options = {-1: "全部"}
        day_options.update({i: DAY_NAMES[i] for i in range(7)})
        selected_day = st.selectbox("筛选星期", options=list(day_options.keys()), format_func=lambda x: day_options[x])
    
    filter_teacher_list = list_teacher if list_teacher > 0 else None
    filter_day = selected_day if selected_day >= 0 else None
    list_schedules = get_all_schedules(headers_tuple, filter_teacher_list, filter_day)
    
    if list_schedules:
        if 'edit_schedule_id' not in st.session_state:
            st.session_state['edit_schedule_id'] = None
        if 'delete_schedule_id' not in st.session_state:
            st.session_state['delete_schedule_id'] = None
        
        st.markdown("### 📊 周课表")
        
        for day_idx in range(7):
            day_schedules = [s for s in list_schedules if s.get('day_of_week') == day_idx]
            
            if day_schedules or filter_day is None:
                with st.expander(f"📅 {DAY_NAMES_FULL[day_idx]} （{len(day_schedules)} 节课）", expanded=(len(day_schedules) > 0)):
                    if day_schedules:
                        day_schedules.sort(key=lambda x: x.get('start_time', ''))
                        for s in day_schedules:
                            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                            with col1:
                                start = s.get('start_time', '')[:5]
                                end = s.get('end_time', '')[:5]
                                st.markdown(f"**{s.get('course_name', '')}**  ⏰ {start}-{end}")
                            with col2:
                                st.markdown(f"📍 {s.get('class_name', '')}  👨‍🏫 {s.get('teacher_name', '')}")
                            with col3:
                                if st.button("✏️", key=f"edit_{s.get('id')}"):
                                    st.session_state['edit_schedule_id'] = s.get('id')
                            with col4:
                                if st.button("🗑️", key=f"del_{s.get('id')}"):
                                    st.session_state['delete_schedule_id'] = s.get('id')
                    else:
                        st.info("暂无课程")
        
        if st.session_state['edit_schedule_id']:
            edit_id = st.session_state['edit_schedule_id']
            edit_schedule = next((s for s in list_schedules if s.get('id') == edit_id), None)
            if edit_schedule:
                st.markdown("---")
                st.markdown("### ✏️ 编辑课程")
                with st.form("edit_form"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        new_course = st.text_input("课程名称", value=edit_schedule.get('course_name', ''))
                        new_class = st.text_input("班级", value=edit_schedule.get('class_name', ''))
                    with e_col2:
                        new_day = st.selectbox("星期", options=list(range(7)), format_func=lambda x: DAY_NAMES[x],
                                               index=edit_schedule.get('day_of_week', 0))
                        orig_start = edit_schedule.get('start_time', '08:00:00')
                        orig_end = edit_schedule.get('end_time', '08:45:00')
                        try:
                            start_h, start_m = int(orig_start[:2]), int(orig_start[3:5])
                            end_h, end_m = int(orig_end[:2]), int(orig_end[3:5])
                        except:
                            start_h, start_m, end_h, end_m = 8, 0, 8, 45
                        new_start = st.time_input("开始时间", value=dt_time(start_h, start_m))
                        new_end = st.time_input("结束时间", value=dt_time(end_h, end_m))
                    
                    btn1, btn2, _ = st.columns([1, 1, 4])
                    with btn1:
                        if st.form_submit_button("💾 保存", type="primary"):
                            update_data = {"course_name": new_course, "class_name": new_class,
                                           "day_of_week": new_day, "start_time": new_start.strftime("%H:%M:%S"),
                                           "end_time": new_end.strftime("%H:%M:%S")}
                            success, msg = update_schedule(edit_id, update_data)
                            if success:
                                # 清除缓存，刷新数据
                                get_all_schedules.clear()
                                get_teachers.clear()
                                st.success("✅ 已更新")
                                st.session_state['edit_schedule_id'] = None
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    with btn2:
                        if st.form_submit_button("取消"):
                            st.session_state['edit_schedule_id'] = None
                            st.rerun()
        
        if st.session_state['delete_schedule_id']:
            del_id = st.session_state['delete_schedule_id']
            del_schedule = next((s for s in list_schedules if s.get('id') == del_id), None)
            if del_schedule:
                st.markdown("---")
                st.warning(f"⚠️ 确定删除 **{del_schedule.get('course_name')}** ?")
                dc1, dc2, _ = st.columns([1, 1, 4])
                with dc1:
                    if st.button("✅ 确认"):
                        success, msg = delete_schedule(del_id)
                        if success:
                            # 清除缓存，刷新数据
                            get_all_schedules.clear()
                            get_teachers.clear()
                            st.success("✅ 已删除")
                            st.session_state['delete_schedule_id'] = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                with dc2:
                    if st.button("❌ 取消"):
                        st.session_state['delete_schedule_id'] = None
                        st.rerun()
    else:
        st.info("📭 暂无课程，请在「新增课程」添加。")

# ==================== Tab3: 新增课程 ====================
with tab3:
    st.markdown("### ➕ 为教师安排新课程")
    
    if not teachers:
        st.warning("暂无教师，请先添加。")
    else:
        with st.form("create_form"):
            c1, c2 = st.columns(2)
            with c1:
                teacher_opts = {t['id']: f"{t['username']} ({t.get('class_name', '')})" for t in teachers}
                sel_teacher = st.selectbox("选择教师 *", options=list(teacher_opts.keys()), format_func=lambda x: teacher_opts[x])
                course_name = st.text_input("课程名称 *", placeholder="数学(代数)")
                class_name = st.text_input("上课班级 *", placeholder="高一(1)班")
            with c2:
                day_of_week = st.selectbox("星期 *", options=list(range(7)), format_func=lambda x: DAY_NAMES_FULL[x])
                start_time = st.time_input("开始时间 *", value=dt_time(8, 0))
                end_time = st.time_input("结束时间 *", value=dt_time(8, 45))
            
            if st.form_submit_button("📝 创建课程", type="primary", use_container_width=True):
                if not course_name or not class_name:
                    st.error("请填写完整信息")
                elif start_time >= end_time:
                    st.error("结束时间须晚于开始时间")
                else:
                    data = {"user_id": sel_teacher, "course_name": course_name, "class_name": class_name,
                            "day_of_week": day_of_week, "start_time": start_time.strftime("%H:%M:%S"),
                            "end_time": end_time.strftime("%H:%M:%S")}
                    success, result = create_schedule(data)
                    if success:
                        # 清除缓存，刷新数据
                        get_all_schedules.clear()
                        get_teachers.clear()
                        st.success("✅ 创建成功！")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")