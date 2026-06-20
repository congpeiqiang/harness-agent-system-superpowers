"""LangGraph 状态图构建。

组装 Supervisor + 5 个专业 Agent 为完整的多 Agent 状态图，
通过 build_agent_graph() 返回编译后的 CompiledGraph。
"""
from langgraph.graph import END, START, StateGraph

from src.agents.aftersale_agent import AfterSaleAgent
from src.agents.general_agent import GeneralAgent
from src.agents.order_agent import OrderAgent
from src.agents.product_agent import ProductAgent
from src.agents.supervisor import AgentState, supervisor_node
from src.agents.user_agent import UserAgent
from src.config.llm_factory import LLMFactory
from src.memory.memory_manager import MemoryManager
from src.mcp_client_service.client.mcp_client import MCPClientManager
from src.observability.logging import get_logger
from src.skills.registry import SkillRegistry

logger = get_logger("graph_builder")


async def build_agent_graph(
    memory: MemoryManager,
    mcp_manager: MCPClientManager,
    skill_registry: SkillRegistry,
):
    """构建并编译多 Agent 状态图。

    Args:
        memory: MemoryManager 实例，提供 checkpointer 和 store。
        mcp_manager: MCPClientManager 实例，提供 MCP 工具。
        skill_registry: SkillRegistry 实例，提供 Skill 工具。

    Returns:
        编译后的 LangGraph CompiledGraph。
    """
    # 实例化各专业 Agent
    product_agent = ProductAgent()
    order_agent = OrderAgent()
    aftersale_agent = AfterSaleAgent()
    general_agent = GeneralAgent(
        extra_tools=mcp_manager.get_tools() + skill_registry.get_all_tools()
    )
    user_agent = UserAgent()

    # 为每个 Agent 创建对应的 LLM 模型
    product_model = LLMFactory.create(agent_name="product")
    order_model = LLMFactory.create(agent_name="order")
    aftersale_model = LLMFactory.create(agent_name="aftersale")
    general_model = LLMFactory.create(agent_name="general")
    user_model = LLMFactory.create(agent_name="user")

    # 封装节点函数，将 model 传递给 invoke_node
    async def product_node(state):
        return await product_agent.invoke_node(state, model=product_model)

    async def order_node(state):
        return await order_agent.invoke_node(state, model=order_model)

    async def aftersale_node(state):
        return await aftersale_agent.invoke_node(state, model=aftersale_model)

    async def general_node(state):
        return await general_agent.invoke_node(state, model=general_model)

    async def user_node(state):
        return await user_agent.invoke_node(state, model=user_model)

    # 构建状态图
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("product", product_node)
    graph.add_node("order", order_node)
    graph.add_node("aftersale", aftersale_node)
    graph.add_node("general", general_node)
    graph.add_node("user", user_node)

    # 入口：START → supervisor
    graph.add_edge(START, "supervisor")

    # 各 Agent 完成后回到 supervisor 进行下一轮路由
    for agent in ["product", "order", "aftersale", "general", "user"]:
        graph.add_edge(agent, "supervisor")

    # 编译：注入持久化层
    checkpointer = await memory.get_checkpointer()
    store = await memory.get_store()
    compiled = graph.compile(checkpointer=checkpointer, store=store)

    logger.info("agent_graph_built", nodes=6)
    return compiled
