"""
视频相关的 Pydantic 模式
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class VideoCreate(BaseModel):
    """视频创建请求（上传时的元数据）"""
    class_name: Optional[str] = Field(None, max_length=50, description="班级名称")
    course_name: Optional[str] = Field(None, max_length=50, description="课程名称")
    lesson_date: Optional[date] = Field(None, description="课程日期")


class VideoResponse(BaseModel):
    """视频详情响应"""
    video_id: int = Field(..., alias="id")
    filename: str
    class_name: Optional[str] = None
    course_name: Optional[str] = None
    lesson_date: Optional[date] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    fps: Optional[float] = None
    resolution: Optional[str] = None
    total_frames: Optional[int] = None
    status: str
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class VideoListItem(BaseModel):
    """视频列表项"""
    video_id: int
    filename: str
    class_name: Optional[str] = None
    course_name: Optional[str] = None
    lesson_date: Optional[date] = None
    duration: Optional[float] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """视频列表响应（带分页）"""
    total: int
    page: int
    page_size: int
    items: List[VideoListItem]


class VideoStatusResponse(BaseModel):
    """视频处理状态响应"""
    video_id: int
    status: str
    progress: float = Field(..., ge=0, le=1, description="处理进度 0-1")
    current_frame: int = 0
    total_frames: Optional[int] = None
    estimated_time_remaining: Optional[int] = None  # 秒
    error_message: Optional[str] = None


class VideoUploadResponse(BaseModel):
    """视频上传响应"""
    task_id: str
    video_id: int
    status: str = "processing"
    message: str = "视频已上传，正在处理中"





