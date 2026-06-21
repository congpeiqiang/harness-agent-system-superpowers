"""deep_agent 审批配置测试。"""
from src.deep_agent.approval import build_interrupt_on, get_approval_tool_names


class _FakeTool:
    def __init__(self, name):
        self.name = name


def test_approval_names_match_settings():
    names = get_approval_tool_names()
    # 与 config/settings.yaml 的 approve_tool_names 一致
    assert "submit_order" in names
    assert "remove_address" in names
    assert "remove_cart_item" in names
    assert "update_profile" in names


def test_build_interrupt_on_only_owned_tools():
    tools = [_FakeTool("submit_order"), _FakeTool("get_order_list")]
    cfg = build_interrupt_on(tools)
    # 只有敏感工具进入审批配置,普通工具不进入
    assert "submit_order" in cfg
    assert "get_order_list" not in cfg


def test_build_interrupt_on_empty_when_no_sensitive():
    tools = [_FakeTool("search_products")]
    assert build_interrupt_on(tools) == {}
