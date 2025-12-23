"""
应用核心配置
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "ClassInsight API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./storage/classinsight.db"
    
    # 文件存储配置
    UPLOAD_DIR: Path = Path("storage/videos")
    MAX_UPLOAD_SIZE: int = 2 * 1024 * 1024 * 1024  # 2GB
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv"]
    
    # 模型配置
    MODEL_WEIGHTS_DIR: Path = Path("ml/weights")
    MODEL_CONFIDENCE_THRESHOLD: float = 0.3
    MODEL_NMS_IOU_THRESHOLD: float = 0.5
    VIDEO_PROCESS_FPS: int = 1  # 每秒提取1帧进行分析
    
    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:8501",  # Streamlit 默认端口
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局类别ID映射（与文档保持一致）
GLOBAL_CATEGORY_MAPPING = {
    # posture (1-2)
    'BowHead': 1,
    'TurnHead': 2,
    
    # learning (3-5)
    'hand-raising': 3,
    'read': 4,
    'write': 5,
    
    # discussion (6)
    'discuss': 6,
    
    # comprehensive (7-14)
    'guide': 7,
    'answer': 8,
    'On-stage interaction': 9,
    'teacher': 10,
    'blackboard-writing': 11,
    'stand': 12,
    'screen': 13,
    'blackBoard': 14
}

# 反向映射：ID -> 名称
ID_TO_CATEGORY = {v: k for k, v in GLOBAL_CATEGORY_MAPPING.items()}

# 行为分类
STUDENT_BEHAVIORS = ['BowHead', 'TurnHead', 'hand-raising', 'read', 'write', 'discuss']
TEACHER_BEHAVIORS = ['guide', 'answer', 'On-stage interaction', 'teacher', 'blackboard-writing', 'stand']
SCENE_ELEMENTS = ['screen', 'blackBoard']

# 模型配置
MODEL_CONFIGS = {
    'comprehensive': {
        'name': 'comprehensive_scene',
        'weight_file': 'comprehensive_scene_best.pt',
        'classes': ['guide', 'answer', 'On-stage interaction', 'blackboard-writing', 
                   'teacher', 'stand', 'screen', 'blackBoard'],
        'class_id_offset': 7  # 全局ID从7开始
    },
    'learning': {
        'name': 'student_learning',
        'weight_file': 'student_learning_best.pt',
        'classes': ['hand-raising', 'read', 'write'],
        'class_id_offset': 3
    },
    'discussion': {
        'name': 'student_discussion',
        'weight_file': 'student_discussion_best.pt',
        'classes': ['discuss'],
        'class_id_offset': 6
    },
    'posture': {
        'name': 'student_posture',
        'weight_file': 'student_posture_best.pt',
        'classes': ['BowHead', 'TurnHead'],
        'class_id_offset': 1
    }
}

# 创建配置实例
settings = Settings()

# 确保必要的目录存在
def init_directories():
    """初始化必要的目录"""
    base_path = Path(__file__).parent.parent.parent
    
    dirs = [
        base_path / "storage",
        base_path / "storage" / "videos",
        base_path / "ml",
        base_path / "ml" / "weights",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)





