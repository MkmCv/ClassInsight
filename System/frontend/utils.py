import os
import streamlit as st

def load_css(file_name="style.css"):
    """
    加载自定义 CSS 文件。
    
    Args:
        file_name (str): CSS 文件名，默认为 'style.css'。
                         函数会自动从 frontend 根目录查找该文件。
    """
    # 获取当前脚本的绝对路径
    current_file = os.path.abspath(__file__)
    # 获取 frontend 目录路径 (当前 utils.py 就在 frontend 目录下)
    frontend_dir = os.path.dirname(current_file)
    
    file_path = os.path.join(frontend_dir, file_name)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS 文件未找到: {file_path}")
    except UnicodeDecodeError:
        st.error(f"CSS 文件编码错误，请确保使用 UTF-8 编码: {file_path}")
    except Exception as e:
        st.error(f"加载 CSS 时发生未知错误: {str(e)}")







