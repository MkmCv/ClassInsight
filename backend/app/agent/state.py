# -*- coding: utf-8 -*-
"""
Agent State 定义

定义 LangGraph Agent 的状态结构，
包含对话历史、分析数据缓存和工作记忆。
"""

from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    课堂分析 Agent 状态
    
    Attributes:
        messages: 对话消息历史（自动累加）
        video_id: 当前分析的视频ID
        summary_data: 行为汇总数据缓存
        timeline_data: 时间线数据缓存
        anomalies_data: 异常事件缓存
        analysis_context: 构建的分析上下文字符串
        identified_issues: 已识别的教学问题
        suggestions_given: 已给出的建议
    """
    
    # 对话消息（LangGraph 内置消息累加器）
    messages: Annotated[List, add_messages]
    
    # 视频标识
    video_id: int
    
    # 数据缓存（避免重复查询数据库）
    summary_data: Optional[Dict[str, Any]]
    timeline_data: Optional[List[Dict[str, Any]]]
    anomalies_data: Optional[List[Dict[str, Any]]]
    
    # 分析上下文（传递给 LLM 的格式化数据）
    analysis_context: Optional[str]
    
    # Agent 工作记忆
    identified_issues: List[str]
    suggestions_given: List[str]


