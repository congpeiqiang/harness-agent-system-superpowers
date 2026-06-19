"""Supervisor Agent — 意图识别与路由。

根据用户消息判断应由哪个专业客服 Agent 处理，
通过 structured_output 输出路由决策，并使用 Command 跳转。
"""
from typing import Literal, TypedDict

from langchain_core.messages import SystemMessage
from langgraph.types import Command

from src.config.llm_factory import LLMFactory
from src.observability.logging import get_logger

logger = get_logger("supervisor")

AGENT_NAMES = Literal["product", "order", "aftersale", "user", "general"]


class RouteDecision(TypedDict):
    """Supervisor 路由决策结构。"""

    target: AGENT_NAMES
    reason: str


class AgentState(TypedDict):
    """LangGraph 状态图中流转的状态。"""

    messages: list
    next_agent: str
    user_id: str
    session_id: str


SUPERVISOR_PROMPT = """你是FecMall商城智能客服调度中心。
根据用户问题判断应由哪个专业客服处理：
- product: 商品搜索、详情、分类、评论、推荐
- order: 购物车、下单、支付、订单查询
- aftersale: 退换货、投诉、售后、FAQ、政策
- user: 账户、地址、登录、注册、个人信息
- general: 天气、汇率、闲聊、其他
只输出路由决策，不要回答用户问题。"""


async def supervisor_node(state: AgentState) -> Command:
    """Supervisor 节点：识别意图并路由到对应专业 Agent。

    Args:
        state: 当前会话状态，包含 messages 等。

    Returns:
        Command，指定跳转到 target agent 并更新 next_agent 字段。
    """
    llm = LLMFactory.create(agent_name="supervisor")
    response = await llm.with_structured_output(schema=RouteDecision).ainvoke(
        [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    )
    target = response["target"]
    logger.info("route_decision", target=target, reason=response.get("reason", ""))
    return Command(update={"next_agent": target}, goto=target)
