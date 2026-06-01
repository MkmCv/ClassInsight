import streamlit as st
import time
import requests
import sys
import os

# 将父目录加入 path 以便导入 utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_css, render_sidebar, check_authentication

st.set_page_config(page_title="上传视频 - ClassInsight", page_icon="📤", layout="wide")

# 引入 CSS
load_css()

# 检查登录（自动从 localStorage 恢复）
check_authentication()

# 渲染侧边栏（用户信息 + 退出登录）
render_sidebar()

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
        elif response.status_code == 404:
            # 视频不存在，可能已经被删除
            return True, "视频不存在（可能已被删除）"
        else:
            try:
                error_msg = response.json().get("detail", "删除失败")
            except:
                error_msg = f"HTTP {response.status_code}"
            return False, error_msg
    except requests.exceptions.ConnectionError:
        # 连接错误：可能是删除成功但没收到响应，需要刷新列表确认
        return None, "无法连接到后端服务，请刷新页面确认删除状态"
    except requests.exceptions.Timeout:
        # 超时：可能是删除成功但响应超时，需要刷新列表确认
        return None, "请求超时，请刷新页面确认删除状态"
    except Exception as e:
        # 其他错误
        return False, f"删除错误: {str(e)}"


def start_video_analysis(video_id):
    """开始分析视频"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/videos/{video_id}/reanalyze",
            headers=get_api_headers(),
            timeout=10
        )
        if response.status_code == 202:
            return True, "分析任务已启动"
        else:
            try:
                error_msg = response.json().get("detail", "启动分析失败")
            except:
                error_msg = f"HTTP {response.status_code}"
            return False, error_msg
    except requests.exceptions.ConnectionError:
        return False, "无法连接到后端服务"
    except requests.exceptions.Timeout:
        return False, "请求超时，请稍后重试"
    except Exception as e:
        return False, f"启动分析错误: {str(e)}"


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

# 初始化状态
if 'delete_confirm' not in st.session_state:
    st.session_state['delete_confirm'] = None
if 'selected_video_id' not in st.session_state:
    st.session_state['selected_video_id'] = None
if 'analyze_confirm' not in st.session_state:
    st.session_state['analyze_confirm'] = None

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
            # 视频选择和分析控制区域
            st.markdown("### 🎯 选择视频进行分析")
            selected_video_option = st.selectbox(
                "选择要分析的视频",
                options=["请选择视频..."] + [f"{v.get('filename', 'N/A')} (ID: {v.get('video_id')}) - {v.get('status', 'unknown')}" for v in videos],
                key="video_selector",
                help="选择一个视频，然后点击下方按钮开始分析"
            )
            
            # 解析选中的视频ID
            if selected_video_option and selected_video_option != "请选择视频...":
                try:
                    # 从选项文本中提取视频ID
                    selected_video_id = None
                    for v in videos:
                        option_text = f"{v.get('filename', 'N/A')} (ID: {v.get('video_id')}) - {v.get('status', 'unknown')}"
                        if selected_video_option == option_text:
                            selected_video_id = v.get('video_id')
                            st.session_state['selected_video_id'] = selected_video_id
                            break
                    
                    if selected_video_id:
                        selected_video = next((v for v in videos if v.get('video_id') == selected_video_id), None)
                        if selected_video:
                            video_status = selected_video.get('status', '')
                            
                            # 显示选中视频的信息
                            st.info(f"""
                            **已选择视频：** {selected_video.get('filename', 'N/A')}
                            
                            - **课程：** {selected_video.get('course_name', '-')} | **班级：** {selected_video.get('class_name', '-')}
                            - **日期：** {selected_video.get('lesson_date', '-')}
                            - **当前状态：** {video_status}
                            """)
                            
                            # 根据状态显示不同的操作选项
                            if video_status == "completed":
                                st.success("✅ 该视频已完成分析，可以查看分析报告")
                                if st.button("📊 查看分析报告", key="view_analysis", use_container_width=True, type="primary"):
                                    st.session_state['current_video_id'] = selected_video_id
                                    st.success("正在跳转到行为分析页面...")
                                    time.sleep(0.5)
                                    st.switch_page("pages/3_📈_行为分析.py")
                            elif video_status == "processing":
                                st.warning("🔄 该视频正在分析中，请等待分析完成")
                                if st.button("🔄 刷新状态", key="refresh_status", use_container_width=True):
                                    st.rerun()
                            elif video_status == "failed":
                                st.error("❌ 该视频分析失败，可以重新开始分析")
                                if st.button("🔄 重新开始分析", key="reanalyze_failed", use_container_width=True, type="primary"):
                                    st.session_state['analyze_confirm'] = selected_video_id
                            elif video_status in ["uploaded", "pending"]:
                                st.info("⏳ 该视频已上传但尚未开始分析")
                                if st.button("🚀 开始分析", key="start_analysis", use_container_width=True, type="primary"):
                                    st.session_state['analyze_confirm'] = selected_video_id
                            else:
                                st.info("该视频可以开始分析")
                                if st.button("🚀 开始分析", key="start_analysis_unknown", use_container_width=True, type="primary"):
                                    st.session_state['analyze_confirm'] = selected_video_id
                except Exception as e:
                    st.error(f"选择视频时出错: {str(e)}")
            
            st.markdown("---")
            
            # 表头
            st.markdown("### 📋 已上传视频列表")
            st.markdown("""
            <div style="display: flex; font-weight: bold; margin-bottom: 10px; padding: 0 5px;">
                <div style="flex: 3;">文件名</div>
                <div style="flex: 2;">课程 | 班级</div>
                <div style="flex: 2;">日期</div>
                <div style="flex: 1;">状态</div>
                <div style="flex: 1.5; text-align: center;">操作</div>
            </div>
            <hr style="margin: 5px 0 15px 0;">
            """, unsafe_allow_html=True)

            for video in videos:
                vid = video.get("video_id")
                video_status = video.get("status", "")
                
                status_emoji = {
                    "uploaded": "⏳",
                    "processing": "🔄",
                    "completed": "✅",
                    "failed": "❌"
                }.get(video_status, "❓")
                
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1.5])
                
                with col1:
                    st.write(f"**{video.get('filename', 'N/A')}**")
                with col2:
                    st.write(f"{video.get('course_name', '-')} | {video.get('class_name', '-')}")
                with col3:
                    st.write(f"{video.get('lesson_date', '-')}")
                with col4:
                    st.write(f"{status_emoji} {video_status}")
                with col5:
                    # 操作按钮列
                    op_col1, op_col2 = st.columns([1, 1])
                    with op_col1:
                        # 只有已完成分析的视频才能查看分析
                        if video_status == "completed":
                            if st.button("📊", key=f"analyze_btn_{vid}", help="查看行为分析"):
                                st.session_state['current_video_id'] = vid
                                st.success(f"已选择视频，正在跳转到行为分析页面...")
                                time.sleep(0.5)
                                st.switch_page("pages/3_📈_行为分析.py")
                        else:
                            # 未完成的视频显示灰色按钮（禁用状态）
                            st.button("📊", key=f"analyze_btn_{vid}_disabled", disabled=True, help="视频分析未完成，无法查看")
                    with op_col2:
                        if st.button("🗑️", key=f"del_btn_{vid}", help="删除该视频"):
                            st.session_state['delete_confirm'] = vid
                
                st.markdown("<div style='height: 1px; background-color: #f0f0f0; margin: 5px 0;'></div>", unsafe_allow_html=True)
            
            # 分析确认对话框
            if st.session_state['analyze_confirm']:
                target_vid = st.session_state['analyze_confirm']
                target_video = next((v for v in videos if v.get('video_id') == target_vid), None)
                
                if target_video:
                    st.warning(f"⚠️ 确定要开始分析视频吗？")
                    st.info(f"""
                    **视频信息：**
                    - 文件名：{target_video.get('filename', 'N/A')}
                    - 课程：{target_video.get('course_name', '-')} | 班级：{target_video.get('class_name', '-')}
                    - 当前状态：{target_video.get('status', 'unknown')}
                    
                    **注意：** 视频分析可能需要较长时间，请耐心等待。
                    """)
                    
                    ac1, ac2 = st.columns([1, 5])
                    with ac1:
                        if st.button("✅ 确认开始分析", key="confirm_analyze", type="primary"):
                            with st.spinner("正在启动分析任务..."):
                                success, msg = start_video_analysis(target_vid)
                                if success:
                                    st.success(f"✅ {msg}")
                                    st.info("💡 提示：分析任务已在后台启动，请稍后刷新页面查看进度。")
                                    st.session_state['analyze_confirm'] = None
                                    st.session_state['selected_video_id'] = None
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                    with ac2:
                        if st.button("❌ 取消", key="cancel_analyze"):
                            st.session_state['analyze_confirm'] = None
                            st.rerun()
            
            # 删除确认对话框
            if st.session_state['delete_confirm']:
                target_vid = st.session_state['delete_confirm']
                st.warning(f"⚠️ 确定要删除视频 (ID: {target_vid}) 吗？此操作不可恢复！")
                
                dc1, dc2 = st.columns([1, 5])
                with dc1:
                    if st.button("✅ 确认删除", key="confirm_del"):
                        success, msg = delete_video(target_vid)
                        if success is None:
                            # 连接错误或超时：可能已删除，需要刷新确认
                            st.warning(f"⚠️ {msg}")
                            st.info("💡 提示：如果视频已从列表中消失，说明删除成功。如果仍然存在，请重试。")
                            st.session_state['delete_confirm'] = None
                            time.sleep(2)
                            st.rerun()
                        elif success:
                            st.success(f"✅ {msg}")
                            st.session_state['delete_confirm'] = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ 删除失败: {msg}")
                with dc2:
                    if st.button("❌ 取消", key="cancel_del"):
                        st.session_state['delete_confirm'] = None
                        st.rerun()

        else:
            st.info("暂无上传的视频")
    elif response.status_code == 401:
        st.error("❌ 认证失败：请重新登录")
        st.info("💡 提示：Token 可能已过期，请退出并重新登录")
    elif response.status_code == 403:
        st.error("❌ 权限不足：无法访问视频列表")
    else:
        try:
            error_detail = response.json().get("detail", f"HTTP {response.status_code}")
        except:
            error_detail = f"HTTP {response.status_code}"
        st.warning(f"获取视频列表失败: {error_detail}")
except requests.exceptions.ConnectionError:
    st.error("❌ 无法连接到后端服务")
    st.info("""
    **可能的原因：**
    1. 后端服务未启动（请检查 http://localhost:8000 是否可访问）
    2. 后端服务地址配置错误
    3. 网络连接问题
    
    **解决方法：**
    - 确认后端服务正在运行
    - 检查 `API_BASE_URL` 环境变量配置
    - 尝试刷新页面
    """)
except requests.exceptions.Timeout:
    st.warning("⏱️ 请求超时，请稍后重试")
    st.info("💡 提示：如果后端服务正在启动，请等待几秒后刷新页面")
except Exception as e:
    st.error(f"❌ 获取视频列表时发生错误: {str(e)}")
    st.info("💡 提示：请检查后端服务状态或联系管理员")