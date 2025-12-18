import streamlit as st
import time
import pandas as pd
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

st.markdown("# 📤 上传课堂视频")
st.markdown("上传新的课堂录像文件，系统将自动进行抽帧、目标检测与行为分析。")

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    with st.container():
        st.markdown("### 1. 选择文件")
        uploaded_file = st.file_uploader("支持 MP4, AVI, MOV 格式", type=['mp4', 'avi', 'mov'])
        
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.1f} MB)")

with col2:
    with st.container():
        st.markdown("### 2. 课程信息")
        class_name = st.text_input("班级", placeholder="例如：高一(1)班")
        course_name = st.text_input("课程名称", placeholder="例如：数学")
        lesson_date = st.date_input("上课日期")

st.markdown("<br>", unsafe_allow_html=True)

if uploaded_file is not None and st.button("🚀 开始上传与分析", type="primary", use_container_width=True):
    progress_text = "正在上传文件..."
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=f"正在上传... {percent_complete + 1}%")
    
    my_bar.empty()
    
    # 模拟处理流程
    st.markdown("### 🔄 AI 处理进度")
    with st.status("正在进行智能分析...", expanded=True) as status:
        st.write("🔍 视频解码与关键帧抽取...")
        time.sleep(1)
        st.write("🧠 加载 VHEAT 模型 (ResNet-50 + FPN)...")
        time.sleep(0.8)
        st.write("👀 多目标检测与行为识别...")
        time.sleep(1.2)
        st.write("📊 生成统计报表与时序数据...")
        time.sleep(0.5)
        status.update(label="✅ 处理完成！", state="complete", expanded=False)
    
    st.balloons()
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("查看分析报告 ->", type="primary", use_container_width=True):
            st.switch_page("pages/3_📈_行为分析.py")


