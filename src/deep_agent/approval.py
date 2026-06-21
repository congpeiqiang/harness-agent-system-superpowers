"""审批配置 —— 把现有配置中的敏感工具映射为 deepagents 的 interrupt_on。

审批工具清单来源与现有系统一致:settings.middleware.human_in_the_loop.approve_tool_names
(当前:submit_order / remove_address / remove_cart_item / update_profile)。
审批就近配置在拥有该工具的子 Agent 上。
"""
from typing import Any

from src.config.settings import get_settings

# 允许的人工决策类型,与现有 HumanInTheLoopMiddleware 用法一致
ALLOWED_DECISIONS = ["approve", "edit", "reject"]


def get_approval_tool_names() -> list[str]:
    """返回需要人工审批的工具名清单(读取现有配置)。"""
    settings = get_settings()
    return list(settings.middleware.human_in_the_loop.approve_tool_names)


def build_interrupt_on(tools: list[Any]) -> dict[str, Any]:
    """为给定子 Agent 的工具生成 interrupt_on 配置。

    只有同时满足「在审批清单中」且「属于该子 Agent」的工具才会被纳入。

    Args:
        tools: 子 Agent 的工具列表(元素需有 .name 属性)。

    Returns:
        {tool_name: {"allowed_decisions": [...]}} 形式的 interrupt_on 字典;
        若该子 Agent 不含任何敏感工具,返回空 dict。
    """
    approval_names = set(get_approval_tool_names())
    interrupt_on: dict[str, Any] = {}
    for tool in tools:
        name = getattr(tool, "name", None)
        if name in approval_names:
            interrupt_on[name] = {"allowed_decisions": list(ALLOWED_DECISIONS)}
    return interrupt_on
