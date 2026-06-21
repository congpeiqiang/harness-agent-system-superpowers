"""Agent 组装器 —— 用 deepagents 的 create_deep_agent 组装主 Agent + 5 子 Agent。

复用 LLMFactory(模型)、MemoryManager(checkpointer/store)、现有全部工具。
返回 CompiledStateGraph,原生支持 ainvoke / astream_events / Command(resume=...)。
"""
from typing import Any

from deepagents import create_deep_agent

from src.config.llm_factory import LLMFactory
from src.deep_agent.subagents import build_subagents
from src.observability.logging import get_logger

logger = get_logger("deep_agent.builder")

# 主 Agent 调度提示词,角色对齐现有 supervisor,但采用 deepagents 的 task 委派范式
SUPERVISOR_PROMPT = (
    "你是 FecMall 商城智能客服调度中心。"
    "请根据用户问题,使用 task 工具委派给合适的专业子客服处理:\n"
    "- product: 商品搜索、详情、分类、评论、推荐\n"
    "- order: 购物车、下单、支付、订单查询\n"
    "- aftersale: 退换货、投诉、售后、FAQ、政策\n"
    "- user: 账户、地址、登录、注册、个人信息\n"
    "- general: 天气、汇率、闲聊、其他\n"
    "对于复杂任务,可拆解为多个子任务分别委派。回答时请使用中文。"
)


async def build_deep_agent(
    *,
    mcp_tools: list[Any],
    skill_tools: list[Any],
    checkpointer: Any,
    store: Any,
) -> Any:
    """构建并返回基于 deepagents 的客服 Agent(CompiledStateGraph)。

    Args:
        mcp_tools: 运行时注入的 MCP 工具(给 general 子 Agent)。
        skill_tools: 运行时注入的 Skill 工具(给 general 子 Agent)。
        checkpointer: 会话级持久化(来自 MemoryManager.get_checkpointer())。
        store: 跨会话长期存储(来自 MemoryManager.get_store())。

    Returns:
        编译好的 deep agent 图。
    """
    model = LLMFactory.create(agent_name="supervisor")
    subagents = build_subagents(mcp_tools=mcp_tools, skill_tools=skill_tools)

    graph = create_deep_agent(
        model=model,
        system_prompt=SUPERVISOR_PROMPT,
        subagents=subagents,
        checkpointer=checkpointer,
        store=store,
    )
    logger.info("deep_agent_built", subagents=len(subagents))
    return graph
