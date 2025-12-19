import streamlit as st
import time
import requests
import sys
import os

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css

st.set_page_config(page_title="上传视频 - ClassInsight", page_icon="📤", layout="wide")

# 引入 CSS
load_css()

if 'authentication_status' not in st.session_state or not st.session_state['authentication_status']:
    st.warning("请先登录")
    st.switch_page("app.py")

# ==================== API 配置 ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def get_api_headers():
    """获取带认证的请求头（不含Content-Type，让requests自动设置）"""
    headers = {}
    if 'access_token' in st.session_state and st.session_state['access_token']:
        headers["Authorization"] = f"Bearer {st.session_state['access_token']}"
    return headers


def upload_video(file, class_name, course_name, lesson_date):
    """上传视频到后端"""
    try:
        files = {"file": (file.name, file.getvalue(), "video/mp4")}
        data = {}
        if class_name:
            data["class_name"] = class_name
        if course_name:
            data["course_name"] = course_name
        if lesson_date:
            data["lesson_date"] = str(lesson_date)
        
        response = requests.post(
            f"{API_BASE_URL}/videos/upload",
            headers=get_api_headers(),
            files=files,
            data=data,
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 202:
            return True, response.json()
        else:
            error_msg = response.json().get("detail", "上传失败")
            return False, error_msg
            
    except requests.exceptions.ConnectionError:
        return False, "无法连接到服务器，请确认后端服务已启动"
    except requests.exceptions.Timeout:
        return False, "上传超时，请检查文件大小或网络连接"
    except Exception as e:
        return False, f"上传错误: {str(e)}"


def check_video_status(video_id):
    """查询视频处理状态"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/videos/{video_id}/status",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def delete_video(video_id):
    """删除视频"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/videos/{video_id}",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code in [200, 204]:  # 兼容 200 OK 和 204 No Content
            return True, "删除成功"
        else:
            try:
                error_msg = response.json().get("detail", "删除失败")
            except:
                error_msg = f"HTTP {response.status_code}"
            return False, error_msg
    except Exception as e:
        return False, str(e)


st.markdown("# 📤 上传课堂视频")
st.markdown("上传新的课堂录像文件，系统将自动进行抽帧、目标检测与行为分析。")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    with st.container():
        st.markdown("### 1. 选择文件")
        uploaded_file = st.file_uploader("支持 MP4, AVI, MOV, MKV 格式（最大 2GB）", type=['mp4', 'avi', 'mov', 'mkv'])
        
        if uploaded_file:
            file_size_mb = uploaded_file.size / 1024 / 1024
            st.success(f"✅ 已选择: {uploaded_file.name} ({file_size_mb:.1f} MB)")

with col2:
    with st.container():
        st.markdown("### 2. 课程信息")
        
        # 自动填充当前用户的班级信息（如果有）
        current_user = st.session_state.get('user', {})
        default_class = current_user.get('class_name', '') if current_user else ''
        default_teacher = current_user.get('username', '') if current_user else ''

        class_name = st.text_input("班级 *", value=default_class, placeholder="例如：高一(1)班")
        course_name = st.text_input("课程名称 *", placeholder="例如：数学")
        teacher_name = st.text_input("授课教师 *", value=default_teacher, placeholder="教师姓名")
        lesson_date = st.date_input("上课日期 *")
        
        st.caption("* 为必填项")

st.markdown("<br>", unsafe_allow_html=True)

# 上传按钮
if uploaded_file is not None:
    if st.button("🚀 开始上传与分析", type="primary", use_container_width=True):
        # 必填项校验
        if not class_name or not course_name or not teacher_name or not lesson_date:
            st.error("❌ 请填写完整的课程信息（班级、课程、教师、日期）后提交")
        else:
            # 上传文件
            with st.spinner("正在上传视频文件..."):
                # 这里可以扩展将 teacher_name 也传给后端
                success, result = upload_video(uploaded_file, class_name, course_name, lesson_date)
            
            if success:
                video_id = result.get("video_id")
                st.success(f"✅ 视频上传成功！视频ID: {video_id}")
                
                # 保存到 session 供其他页面使用
                st.session_state['current_video_id'] = video_id
                
                # 显示处理进度
                st.markdown("### 🔄 AI 处理进度")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 轮询处理状态
                max_wait = 600  # 最多等待10分钟
                wait_time = 0
                
                while wait_time < max_wait:
                    status_data = check_video_status(video_id)
                    
                    if status_data:
                        progress = status_data.get("progress", 0)
                        status = status_data.get("status", "processing")
                        
                        progress_bar.progress(progress)
                        
                        if status == "completed":
                            status_text.success("✅ 处理完成！")
                            st.balloons()
                            break
                        elif status == "failed":
                            error_msg = status_data.get("error_message", "未知错误")
                            status_text.error(f"❌ 处理失败: {error_msg}")
                            break
                        else:
                            current_frame = status_data.get("current_frame", 0)
                            total_frames = status_data.get("total_frames", 0)
                            if total_frames > 0:
                                status_text.info(f"🔄 正在分析... 进度: {progress*100:.1f}% ({current_frame}/{total_frames} 帧)")
                            else:
                                status_text.info(f"🔄 正在分析... 进度: {progress*100:.1f}%")
                    
                    time.sleep(2)  # 每2秒查询一次
                    wait_time += 2
                
                if wait_time >= max_wait:
                    status_text.warning("⏱️ 处理时间较长，请稍后在视频列表中查看状态")
                
                # 完成后显示操作按钮
                st.markdown("<br>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1, 1, 1])
                with c2:
                    if st.button("查看分析报告 →", type="primary", use_container_width=True):
                        st.switch_page("pages/3_📈_行为分析.py")
            else:
                st.error(f"❌ {result}")

# 显示已上传的视频列表
st.markdown("---")
st.markdown("### 📋 已上传视频")

# 初始化删除状态
if 'delete_confirm' not in st.session_state:
    st.session_state['delete_confirm'] = None

try:
    response = requests.get(
        f"{API_BASE_URL}/videos",
        headers=get_api_headers(),
        params={"page": 1, "page_size": 10},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        videos = data.get("items", [])
        
        if videos:
            # 表头
            st.markdown("""
            <div style="display: flex; font-weight: bold; margin-bottom: 10px; padding: 0 5px;">
                <div style="flex: 3;">文件名</div>
                <div style="flex: 2;">课程 | 班级</div>
                <div style="flex: 2;">日期</div>
                <div style="flex: 1;">状态</div>
                <div style="flex: 1; text-align: center;">操作</div>
            </div>
            <hr style="margin: 5px 0 15px 0;">
            """, unsafe_allow_html=True)

            for video in videos:
                vid = video.get("video_id")
                
                status_emoji = {
                    "uploaded": "⏳",
                    "processing": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(video.get("status"), "❓")
                
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                
                with col1:
                    st.write(f"**{video.get('filename', 'N/A')}**")
                with col2:
                    st.write(f"{video.get('course_name', '-')} | {video.get('class_name', '-')}")
                with col3:
                    st.write(f"{video.get('lesson_date', '-')}")
                with col4:
                    st.write(f"{status_emoji} {video.get('status', '-')}")
                with col5:
                    if st.button("🗑️", key=f"del_btn_{vid}", help="删除该视频"):
                        st.session_state['delete_confirm'] = vid
                
                st.markdown("<div style='height: 1px; background-color: #f0f0f0; margin: 5px 0;'></div>", unsafe_allow_html=True)
            
            # 删除确认对话框
            if st.session_state['delete_confirm']:
                target_vid = st.session_state['delete_confirm']
                st.warning(f"⚠️ 确定要删除视频 (ID: {target_vid}) 吗？此操作不可恢复！")
                
                dc1, dc2 = st.columns([1, 5])
                with dc1:
                    if st.button("✅ 确认删除", key="confirm_del"):
                        success, msg = delete_video(target_vid)
                        if success:
                            st.success(f"视频已删除")
                            st.session_state['delete_confirm'] = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"删除失败: {msg}")
                with dc2:
                    if st.button("❌ 取消", key="cancel_del"):
                        st.session_state['delete_confirm'] = None
                        st.rerun()

        else:
            st.info("暂无上传的视频")
    else:
        st.warning("获取视频列表失败")
except:
    st.warning("无法连接后端服务")
