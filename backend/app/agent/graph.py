# -*- coding: utf-8 -*-
"""
LangGraph Agent 工作流

基于通义千问实现的教学顾问 Agent，
支持多轮对话和工具调用。
"""

import os
import logging
from typing import Literal
import dashscope
from dashscope import Generation
from langgraph.graph import StateGraph, END

from .state import AgentState
from .prompts import SYSTEM_PROMPT, INITIAL_ANALYSIS_PROMPT
from .tools import (
    get_behavior_summary,
    get_behavior_timeline,
    get_anomaly_events,
    format_summary_for_prompt,
    format_timeline_for_prompt,
    format_anomalies_for_prompt
)

logger = logging.getLogger(__name__)

# 从环境变量获取 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-1d60868c52764ce09581a21d403aabe5")
dashscope.api_key = DASHSCOPE_API_KEY


async def load_analysis_data(state: AgentState) -> AgentState:
    """
    节点1: 加载分析数据
    
    从数据库获取视频的分析数据并缓存到状态中
    """
    video_id = state["video_id"]
    logger.info(f"加载视频 {video_id} 的分析数据")
    
    # 并行获取所有数据
    summary = await get_behavior_summary(video_id)
    timeline = await get_behavior_timeline(video_id)
    anomalies = await get_anomaly_events(video_id)
    
    # 构建分析上下文
    context = f"""
{format_summary_for_prompt(summary)}

【时间趋势分析】
{format_timeline_for_prompt(timeline)}

【异常事件】
{format_anomalies_for_prompt(anomalies)}
"""
    
    return {
        **state,
        "summary_data": summary,
        "timeline_data": timeline,
        "anomalies_data": anomalies,
        "analysis_context": context
    }


async def generate_response(state: AgentState) -> AgentState:
    """
    节点2: 生成回复
    
    调用通义千问生成回复
    """
    messages = state["messages"]
    context = state.get("analysis_context", "暂无分析数据")
    
    # 构建完整的消息列表
    system_message = SYSTEM_PROMPT + f"\n\n## 当前课堂数据\n{context}"
    
    # 转换消息格式
    qwen_messages = [{"role": "system", "content": system_message}]
    
    for msg in messages:
        if hasattr(msg, "content"):
            role = "user" if msg.type == "human" else "assistant"
            qwen_messages.append({"role": role, "content": msg.content})
        elif isinstance(msg, dict):
            qwen_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    
    logger.info(f"调用通义千问，消息数: {len(qwen_messages)}")
    
    try:
        response = Generation.call(
            model="qwen-plus",  # 使用 qwen-plus 获得更好的分析能力
            messages=qwen_messages,
            result_format='message',
            temperature=0.7,
            max_tokens=1500
        )
        
        if response.status_code == 200:
            assistant_content = response.output.choices[0].message.content
            logger.info(f"生成回复成功，长度: {len(assistant_content)}")
        else:
            logger.error(f"API 调用失败: {response.code} - {response.message}")
            assistant_content = f"抱歉，AI 服务暂时不可用（错误码: {response.code}）。请稍后重试。"
            
    except Exception as e:
        logger.exception(f"生成回复失败: {e}")
        assistant_content = f"抱歉，处理请求时发生错误: {str(e)}"
    
    # 添加助手回复到消息列表
    from langchain_core.messages import AIMessage
    new_messages = list(messages) + [AIMessage(content=assistant_content)]
    
    return {
        **state,
        "messages": new_messages
    }


def should_load_data(state: AgentState) -> Literal["load_data", "generate"]:
    """
    路由: 判断是否需要加载数据
    
    如果数据未缓存，先加载数据
    """
    if state.get("summary_data") is None:
        return "load_data"
    return "generate"


def create_agent_graph():
    """
    创建 Agent 工作流图
    
    流程:
    1. 检查是否需要加载数据
    2. 如需要，从数据库加载分析数据
    3. 调用 LLM 生成回复
    """
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("load_data", load_analysis_data)
    workflow.add_node("generate", generate_response)
    
    # 设置入口点和条件路由
    workflow.set_entry_point("load_data")
    
    # load_data 完成后进入 generate
    workflow.add_edge("load_data", "generate")
    
    # generate 完成后结束
    workflow.add_edge("generate", END)
    
    return workflow.compile()


# 创建全局 Agent 实例
classroom_agent = create_agent_graph()


async def chat_with_agent(video_id: int, user_message: str, history: list = None) -> str:
    """
    与 Agent 对话的便捷函数
    
    Args:
        video_id: 视频ID
        user_message: 用户消息
        history: 历史消息列表（可选）
        
    Returns:
        Agent 回复内容
    """
    from langchain_core.messages import HumanMessage
    
    # 构建初始状态
    messages = []
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg["content"]))
    
    messages.append(HumanMessage(content=user_message))
    
    initial_state: AgentState = {
        "messages": messages,
        "video_id": video_id,
        "summary_data": None,
        "timeline_data": None,
        "anomalies_data": None,
        "analysis_context": None,
        "identified_issues": [],
        "suggestions_given": []
    }
    
    # 运行 Agent
    result = await classroom_agent.ainvoke(initial_state)
    
    # 提取最后一条助手消息
    last_message = result["messages"][-1]
    return last_message.content if hasattr(last_message, "content") else str(last_message)


















