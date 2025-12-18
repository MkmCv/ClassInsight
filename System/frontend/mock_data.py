import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==================== 模拟用户数据 ====================
MOCK_USER = {
    "id": 1,
    "username": "teacher001",
    "email": "teacher@example.com",
    "role": "teacher",
    "unit": "岭南师范学院",
    "class_name": "高一(1)班",
    "created_at": "2025-10-23T10:00:00Z"
}

# ==================== 模拟视频列表 ====================
MOCK_VIDEOS = [
    {
        "video_id": 1,
        "filename": "class_math_20251023.mp4",
        "class_name": "高一(1)班",
        "course_name": "数学",
        "lesson_date": "2025-10-23",
        "duration": 2700, # 45分钟
        "status": "completed",
        "created_at": "2025-10-23T10:00:00Z",
        "fps": 30.0,
        "resolution": "1920x1080"
    },
    {
        "video_id": 2,
        "filename": "class_english_20251024.mp4",
        "class_name": "高一(1)班",
        "course_name": "英语",
        "lesson_date": "2025-10-24",
        "duration": 2700,
        "status": "processing",
        "progress": 0.65,
        "created_at": "2025-10-24T09:00:00Z",
        "fps": 30.0,
        "resolution": "1920x1080"
    },
    {
        "video_id": 3,
        "filename": "class_physics_20251022.mp4",
        "class_name": "高一(1)班",
        "course_name": "物理",
        "lesson_date": "2025-10-22",
        "duration": 2800,
        "status": "completed",
        "created_at": "2025-10-22T14:00:00Z",
        "fps": 30.0,
        "resolution": "1920x1080"
    }
]

# ==================== 模拟行为统计（整课） ====================
def get_mock_summary(video_id):
    return {
        "video_id": video_id,
        "duration": 2700,
        "total_frames": 81000,
        "behavior_summary": {
            "discuss": {"count": 45, "total_duration": 800, "percentage": 29.6},
            "hand-raising": {"count": 12, "total_duration": 180, "percentage": 6.7},
            "read": {"count": 150, "total_duration": 1200, "percentage": 44.4},
            "write": {"count": 80, "total_duration": 600, "percentage": 22.2},
            "BowHead": {"count": 30, "total_duration": 300, "percentage": 11.1},
            "TurnHead": {"count": 15, "total_duration": 100, "percentage": 3.7}
        },
        "teacher_behavior": {
            "teacher": {"count": 1, "duration": 2700, "percentage": 100.0},
            "blackboard-writing": {"count": 8, "duration": 600, "percentage": 22.2},
            "screen": {"count": 5, "duration": 1200, "percentage": 44.4},
            "guide": {"count": 20, "duration": 900, "percentage": 33.3},
            "answer": {"count": 15, "duration": 300, "percentage": 11.1}
        }
    }

# ==================== 模拟时间序列数据 ====================
def get_mock_timeline(video_id, window=60):
    # 生成45分钟的模拟数据
    duration = 45 * 60
    steps = duration // window
    
    data = []
    for i in range(steps):
        timestamp = i * window
        # 模拟一些随时间变化的趋势
        base_discuss = 5 + np.sin(i/5) * 3
        base_read = 15 + np.cos(i/8) * 5
        
        entry = {
            "timestamp": timestamp,
            "behaviors": {
                "discuss": int(max(0, base_discuss + np.random.randint(-2, 3))),
                "hand-raising": int(max(0, np.random.randint(0, 3))),
                "read": int(max(0, base_read + np.random.randint(-3, 4))),
                "write": int(max(0, 10 + np.random.randint(-2, 3))),
                "BowHead": int(max(0, 5 + np.random.randint(-2, 5))), # 偶尔有异常高值
                "TurnHead": int(max(0, 2 + np.random.randint(-1, 2)))
            }
        }
        data.append(entry)
    
    return {
        "video_id": video_id,
        "window_size": window,
        "timeline": data
    }

# ==================== 模拟异常检测 ====================
def get_mock_anomalies(video_id):
    return {
        "video_id": video_id,
        "anomalies": [
            {
                "start_time": 1200,
                "end_time": 1380,
                "type": "high_bowhead_rate",
                "severity": "medium",
                "description": "低头率持续偏高（>30%），持续3分钟",
                "behavior_stats": {
                    "BowHead": {"count": 45, "percentage": 35.0}
                }
            },
            {
                "start_time": 600,
                "end_time": 720,
                "type": "low_interaction",
                "severity": "low",
                "description": "连续2分钟无师生互动",
                "behavior_stats": {}
            }
        ]
    }

# ==================== 模拟优化建议 ====================
def get_mock_recommendations(video_id):
    return {
        "video_id": video_id,
        "recommendations": [
            {
                "type": "interaction",
                "priority": "high",
                "title": "增加互动频次",
                "description": "课程中段（20-30分钟）讨论占比不足15%，建议增加分组讨论。",
                "suggested_actions": [
                    "在讲解完核心概念后，设置3-5分钟的小组讨论",
                    "使用随机提问工具激活课堂气氛"
                ]
            },
            {
                "type": "attention",
                "priority": "medium",
                "title": "关注学生疲劳度",
                "description": "第25分钟左右低头率出现峰值，可能是内容过于枯燥或学生疲劳。",
                "suggested_actions": [
                    "插入一个相关视频案例吸引注意力",
                    "进行简单的课堂伸展活动"
                ]
            }
        ]
    }

# ==================== 模拟精彩片段 ====================
def get_mock_highlights(video_id):
    return {
        "video_id": video_id,
        "highlights": [
            {
                "start_time": 800,
                "end_time": 950,
                "score": 0.92,
                "reasons": ["互动占比高（35%）", "低头率极低（<5%）"],
                "description": "高质量的分组讨论环节"
            },
            {
                "start_time": 1500,
                "end_time": 1600,
                "score": 0.88,
                "reasons": ["教师引导与学生响应配合紧密"],
                "description": "精彩的师生问答"
            }
        ]
    }


