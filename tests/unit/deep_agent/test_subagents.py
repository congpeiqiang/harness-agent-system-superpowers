"""deep_agent 子 Agent 定义测试。"""
from src.deep_agent.subagents import build_subagents


def test_five_subagents_with_expected_names():
    subs = build_subagents(mcp_tools=[], skill_tools=[])
    names = {s["name"] for s in subs}
    assert names == {"product", "order", "aftersale", "user", "general"}


def test_each_subagent_has_required_fields():
    subs = build_subagents(mcp_tools=[], skill_tools=[])
    for s in subs:
        assert s["name"]
        assert s["description"]
        assert s["system_prompt"]
        assert "tools" in s


def test_order_subagent_has_approval_on_submit_order():
    subs = {s["name"]: s for s in build_subagents(mcp_tools=[], skill_tools=[])}
    order = subs["order"]
    assert "submit_order" in order["interrupt_on"]


def test_product_subagent_has_no_approval():
    subs = {s["name"]: s for s in build_subagents(mcp_tools=[], skill_tools=[])}
    # 商品子 Agent 无敏感工具,interrupt_on 为空
    assert subs["product"]["interrupt_on"] == {}


def test_general_subagent_receives_injected_tools():
    subs = {s["name"]: s for s in build_subagents(mcp_tools=["M"], skill_tools=["S"])}
    assert "M" in subs["general"]["tools"]
    assert "S" in subs["general"]["tools"]
