# -*- coding: utf-8 -*-
"""
ClassInsight AI Agent 模块

基于 LangGraph 实现的教学顾问 Agent，
能够分析课堂行为数据并给出个性化教学建议。
"""

from .graph import create_agent_graph
from .state import AgentState

__all__ = ["create_agent_graph", "AgentState"]


