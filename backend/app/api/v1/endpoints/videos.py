"""
视频管理 API 路由
"""
import os
import uuid
import aiofiles
from datetime import datetime, date
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ....core.database import get_db
from ....core.config import settings
from ....models.user import User
from ....models.video import Video, VideoStatus
from ....schemas.video import (
    VideoResponse, VideoListResponse, VideoListItem, 
    VideoStatusResponse, VideoUploadResponse
)
from ...deps import get_current_user
from ....services.video_processor import process_video_task

router = APIRouter()


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    class_name: Optional[str] = Form(None),
    course_name: Optional[str] = Form(None),
    lesson_date: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传视频文件并创建处理任务
    """
    # 验证文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式。支持的格式: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    # 生成唯一文件名
    task_id = str(uuid.uuid4())
    safe_filename = f"{task_id}{file_ext}"
    
    # 确保上传目录存在
    upload_dir = Path(__file__).parent.parent.parent.parent.parent / "storage" / "videos"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / safe_filename
    
    # 保存文件
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        file_size = len(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )
    
    # 解析日期
    parsed_date = None
    if lesson_date:
        try:
            parsed_date = datetime.strptime(lesson_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    
    # 创建视频记录
    video = Video(
        user_id=current_user.id,
        filename=file.filename,
        filepath=str(file_path),
        file_size=file_size,
        class_name=class_name,
        course_name=course_name,
        lesson_date=parsed_date,
        status=VideoStatus.PROCESSING.value
    )
    
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # 启动后台处理任务
    background_tasks.add_task(process_video_task, video.id, str(file_path))
    
    return VideoUploadResponse(
        task_id=task_id,
        video_id=video.id,
        status="processing",
        message="视频已上传，正在处理中"
    )


@router.get("", response_model=VideoListResponse)
async def get_video_list(
    page: int = 1,
    page_size: int = 20,
    class_name: Optional[str] = None,
    course_name: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频列表（带分页和筛选）
    """
    # 构建查询条件
    conditions = [Video.user_id == current_user.id]
    
    if class_name:
        conditions.append(Video.class_name == class_name)
    if course_name:
        conditions.append(Video.course_name == course_name)
    if status_filter:
        conditions.append(Video.status == status_filter)
    
    # 查询总数
    count_result = await db.execute(
        select(func.count(Video.id)).where(and_(*conditions))
    )
    total = count_result.scalar() or 0
    
    # 分页查询
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Video)
        .where(and_(*conditions))
        .order_by(Video.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    videos = result.scalars().all()
    
    items = [
        VideoListItem(
            video_id=v.id,
            filename=v.filename,
            class_name=v.class_name,
            course_name=v.course_name,
            lesson_date=v.lesson_date,
            duration=v.duration,
            status=v.status,
            created_at=v.created_at
        )
        for v in videos
    ]
    
    return VideoListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video_detail(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频详情
    """
    result = await db.execute(
        select(Video).where(
            and_(Video.id == video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    return VideoResponse(
        id=video.id,
        filename=video.filename,
        class_name=video.class_name,
        course_name=video.course_name,
        lesson_date=video.lesson_date,
        duration=video.duration,
        file_size=video.file_size,
        fps=video.fps,
        resolution=video.resolution,
        total_frames=video.total_frames,
        status=video.status,
        user_id=video.user_id,
        created_at=video.created_at
    )


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
async def get_video_status(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询视频处理状态
    """
    result = await db.execute(
        select(Video).where(
            and_(Video.id == video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    # 估算剩余时间
    estimated_time = None
    if video.status == VideoStatus.PROCESSING.value and video.progress > 0:
        # 简单估算：已用时间 / 进度 * 剩余进度
        elapsed = (datetime.utcnow() - video.created_at).total_seconds()
        if video.progress > 0:
            estimated_time = int(elapsed / video.progress * (1 - video.progress))
    
    return VideoStatusResponse(
        video_id=video.id,
        status=video.status,
        progress=video.progress,
        current_frame=video.current_frame,
        total_frames=video.total_frames,
        estimated_time_remaining=estimated_time,
        error_message=video.error_message
    )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除视频及其所有相关数据
    """
    result = await db.execute(
        select(Video).where(
            and_(Video.id == video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    # 删除物理文件
    try:
        if os.path.exists(video.filepath):
            os.remove(video.filepath)
    except Exception:
        pass  # 忽略文件删除错误
    
    # 删除数据库记录（级联删除关联数据）
    await db.delete(video)
    await db.commit()
    
    return None


@router.post("/{video_id}/reanalyze", status_code=status.HTTP_202_ACCEPTED)
async def reanalyze_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重新分析视频
    对于已上传但未分析、分析失败或需要重新分析的视频，可以触发重新分析
    """
    result = await db.execute(
        select(Video).where(
            and_(Video.id == video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在"
        )
    
    # 检查视频文件是否存在
    if not os.path.exists(video.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频文件不存在，无法重新分析"
        )
    
    # 检查视频状态：如果正在处理中，不允许重新分析
    if video.status == VideoStatus.PROCESSING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频正在处理中，请等待处理完成"
        )
    
    # 更新状态为处理中
    video.status = VideoStatus.PROCESSING.value
    video.progress = 0.0
    video.current_frame = 0
    video.error_message = None
    await db.commit()
    
    # 启动后台处理任务
    background_tasks.add_task(process_video_task, video.id, video.filepath)
    
    return {
        "message": "视频分析任务已启动",
        "video_id": video.id,
        "status": "processing"
    }





