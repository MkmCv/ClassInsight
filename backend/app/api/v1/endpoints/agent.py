# -*- coding: utf-8 -*-
"""
AI Agent API 路由

提供教学顾问 Agent 的对话接口
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio

from ....core.database import get_db
from ....models.user import User
from ....models.video import Video, VideoStatus
from ...deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # "user" 或 "assistant"
    content: str


class ChatRequest(BaseModel):
    """聊天请求"""
    video_id: int
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    video_id: int


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    与 AI 教学顾问对话
    
    - **video_id**: 当前分析的视频ID
    - **messages**: 对话历史消息列表
    """
    from ....agent.graph import chat_with_agent as agent_chat
    from sqlalchemy import select, and_
    
    # 验证视频访问权限
    result = await db.execute(
        select(Video).where(
            and_(Video.id == request.video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在或无权访问"
        )
    
    if video.status != VideoStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="视频尚未完成分析，请等待处理完成"
        )
    
    # 提取用户最后一条消息
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供用户消息"
        )
    
    last_user_message = user_messages[-1].content
    
    # 构建历史消息
    history = [{"role": m.role, "content": m.content} for m in request.messages[:-1]]
    
    try:
        # 调用 Agent
        response_content = await agent_chat(
            video_id=request.video_id,
            user_message=last_user_message,
            history=history
        )
        
        return ChatResponse(
            content=response_content,
            video_id=request.video_id
        )
        
    except Exception as e:
        logger.exception(f"Agent 调用失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务暂时不可用: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_with_agent_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    与 AI 教学顾问对话（流式输出）
    
    返回 Server-Sent Events 格式的流式响应
    """
    from ....agent.graph import chat_with_agent as agent_chat
    from sqlalchemy import select, and_
    
    # 验证视频访问权限
    result = await db.execute(
        select(Video).where(
            and_(Video.id == request.video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在或无权访问"
        )
    
    # 提取用户最后一条消息
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供用户消息"
        )
    
    last_user_message = user_messages[-1].content
    history = [{"role": m.role, "content": m.content} for m in request.messages[:-1]]
    
    async def generate():
        try:
            # 先发送开始信号
            yield f"data: {json.dumps({'status': 'start'})}\n\n"
            
            # 调用 Agent 获取完整回复
            response_content = await agent_chat(
                video_id=request.video_id,
                user_message=last_user_message,
                history=history
            )
            
            # 模拟流式输出（按字符发送）
            for i in range(0, len(response_content), 5):  # 每次发送5个字符
                chunk = response_content[i:i+5]
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                await asyncio.sleep(0.02)  # 小延迟使效果更自然
            
            # 发送结束信号
            yield f"data: {json.dumps({'status': 'done'})}\n\n"
            
        except Exception as e:
            logger.exception(f"流式 Agent 调用失败: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/context/{video_id}")
async def get_analysis_context(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频的分析上下文（调试用）
    
    返回 Agent 将使用的分析数据摘要
    """
    from ....agent.tools import (
        get_behavior_summary,
        get_behavior_timeline,
        get_anomaly_events,
        format_summary_for_prompt,
        format_timeline_for_prompt,
        format_anomalies_for_prompt
    )
    from sqlalchemy import select, and_
    
    # 验证权限
    result = await db.execute(
        select(Video).where(
            and_(Video.id == video_id, Video.user_id == current_user.id)
        )
    )
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="视频不存在或无权访问"
        )
    
    # 获取数据
    summary = await get_behavior_summary(video_id)
    timeline = await get_behavior_timeline(video_id)
    anomalies = await get_anomaly_events(video_id)
    
    return {
        "video_id": video_id,
        "raw_data": {
            "summary": summary,
            "timeline_points": len(timeline),
            "anomalies_count": len(anomalies)
        },
        "formatted_context": {
            "summary": format_summary_for_prompt(summary),
            "timeline": format_timeline_for_prompt(timeline),
            "anomalies": format_anomalies_for_prompt(anomalies)
        }
    }


