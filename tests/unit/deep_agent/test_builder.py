"""deep_agent 组装器测试 —— 用 mock 模型,不发真实请求。"""
from unittest.mock import patch

import pytest

from src.deep_agent.builder import build_deep_agent


class _FakeModel:
    """占位模型,组装阶段不会真正调用它。"""


@pytest.mark.asyncio
async def test_build_deep_agent_returns_compiled_graph():
    captured = {}

    def fake_create_deep_agent(**kwargs):
        captured.update(kwargs)
        return "COMPILED_GRAPH"

    with patch("src.deep_agent.builder.LLMFactory.create", return_value=_FakeModel()), \
         patch("src.deep_agent.builder.create_deep_agent", side_effect=fake_create_deep_agent):
        result = await build_deep_agent(
            mcp_tools=[], skill_tools=[], checkpointer="CP", store="ST"
        )

    assert result == "COMPILED_GRAPH"
    # 5 个子 Agent 已传入
    assert len(captured["subagents"]) == 5
    # 持久化层透传
    assert captured["checkpointer"] == "CP"
    assert captured["store"] == "ST"
    # 主 Agent 系统提示词非空
    assert captured["system_prompt"]
