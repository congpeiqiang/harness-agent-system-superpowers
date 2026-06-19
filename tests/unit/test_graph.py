"""Tests for Supervisor routing and LangGraph state graph."""
import pytest


class TestRouteDecision:
    """RouteDecision TypedDict 结构验证。"""

    def test_route_decision_product(self):
        from src.agents.supervisor import RouteDecision
        decision = RouteDecision(target="product", reason="用户询问商品信息")
        assert decision["target"] == "product"
        assert decision["target"] in ["product", "order", "aftersale", "user", "general"]

    def test_route_decision_order(self):
        from src.agents.supervisor import RouteDecision
        decision = RouteDecision(target="order", reason="用户查询订单")
        assert decision["target"] == "order"
        assert decision["reason"] == "用户查询订单"

    def test_route_decision_aftersale(self):
        from src.agents.supervisor import RouteDecision
        decision = RouteDecision(target="aftersale", reason="用户需要退换货")
        assert decision["target"] == "aftersale"

    def test_route_decision_user(self):
        from src.agents.supervisor import RouteDecision
        decision = RouteDecision(target="user", reason="用户修改地址")
        assert decision["target"] == "user"

    def test_route_decision_general(self):
        from src.agents.supervisor import RouteDecision
        decision = RouteDecision(target="general", reason="闲聊")
        assert decision["target"] == "general"


class TestAgentNames:
    """AGENT_NAMES Literal 类型验证。"""

    def test_agent_names_is_literal(self):
        from typing import get_args
        from src.agents.supervisor import AGENT_NAMES
        names = get_args(AGENT_NAMES)
        assert "product" in names
        assert "order" in names
        assert "aftersale" in names
        assert "user" in names
        assert "general" in names
        assert len(names) == 5


class TestAgentState:
    """AgentState TypedDict 结构验证。"""

    def test_agent_state_keys(self):
        from src.agents.supervisor import AgentState
        state = AgentState(
            messages=[],
            next_agent="product",
            user_id="u123",
            session_id="s456",
        )
        assert state["messages"] == []
        assert state["next_agent"] == "product"
        assert state["user_id"] == "u123"
        assert state["session_id"] == "s456"

    def test_agent_state_has_required_keys(self):
        from src.agents.supervisor import AgentState
        annotations = AgentState.__annotations__
        assert "messages" in annotations
        assert "next_agent" in annotations
        assert "user_id" in annotations
        assert "session_id" in annotations


class TestSupervisorPrompt:
    """Supervisor 系统提示词验证。"""

    def test_supervisor_prompt_contains_agent_names(self):
        from src.agents.supervisor import SUPERVISOR_PROMPT
        for agent in ["product", "order", "aftersale", "user", "general"]:
            assert agent in SUPERVISOR_PROMPT, f"Missing agent '{agent}' in prompt"

    def test_supervisor_prompt_is_nonempty(self):
        from src.agents.supervisor import SUPERVISOR_PROMPT
        assert len(SUPERVISOR_PROMPT) > 0


class TestSupervisorNode:
    """supervisor_node 函数验证。"""

    def test_supervisor_node_is_callable(self):
        from src.agents.supervisor import supervisor_node
        assert callable(supervisor_node)

    def test_supervisor_node_is_async(self):
        import asyncio
        from src.agents.supervisor import supervisor_node
        assert asyncio.iscoroutinefunction(supervisor_node)


class TestGraphBuilder:
    """build_agent_graph 函数验证。"""

    def test_build_agent_graph_is_importable(self):
        from src.agents.graph_builder import build_agent_graph
        assert callable(build_agent_graph)

    def test_build_agent_graph_is_async(self):
        import asyncio
        from src.agents.graph_builder import build_agent_graph
        assert asyncio.iscoroutinefunction(build_agent_graph)
