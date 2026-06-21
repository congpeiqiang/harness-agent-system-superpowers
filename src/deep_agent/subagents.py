"""子 Agent 定义 —— 5 个 SubAgent,镜像现有 src/agents 下 5 个专业 Agent。

每个子 Agent 的系统提示词与工具均与对应的现有专业 Agent 保持一致,
审批通过 interrupt_on 就近配置在拥有敏感工具的子 Agent 上。
"""
from typing import Any

from src.deep_agent.approval import build_interrupt_on
from src.deep_agent.tools import (
    get_aftersale_tools,
    get_general_tools,
    get_order_tools,
    get_product_tools,
    get_user_tools,
)

# 系统提示词与现有专业 Agent 对齐(见 src/agents/*_agent.py)
PRODUCT_PROMPT = (
    "你是一个专业的电商商品助手。你可以帮助用户搜索商品、查看商品详情、"
    "浏览分类商品、阅读商品评论以及获取首页推荐信息。"
    "请根据用户的需求,使用合适的工具为他们提供准确的商品信息。"
    "回答时请使用中文,并对商品信息做出清晰的总结和推荐。"
)
ORDER_PROMPT = (
    "你是一个专业的电商订单助手。你可以帮助用户管理购物车(添加、修改、删除商品)、"
    "查看购物车内容、初始化结算、提交订单、查看订单列表和订单详情。"
    "请在执行敏感操作(如提交订单、删除商品)前向用户确认。"
    "回答时请使用中文,并对订单信息做出清晰的总结。"
)
AFTERSALE_PROMPT = (
    "你是一个专业的电商售后助手。你可以帮助用户提交售后投诉、查询订单退款状态,"
    "以及从知识库中搜索退换货政策和常见问题。"
    "在处理投诉时请耐心倾听用户的问题,并提供清晰的解决方案。"
    "回答时请使用中文,语气友好且有同理心。"
)
USER_PROMPT = (
    "你是一个专业的用户账户助手。你可以帮助用户登录、注册新账户、"
    "查看和更新个人资料,以及管理收货地址(添加、查看、删除)。"
    "请在执行敏感操作(如修改资料、删除地址)前向用户确认。"
    "回答时请使用中文,注意保护用户的隐私信息。"
)
GENERAL_PROMPT = (
    "你是一个通用的智能助手。你可以使用各种外部工具来帮助用户完成任务,"
    "包括天气查询、货币转换等功能。"
    "请根据用户的需求选择合适的工具,并提供准确的信息。"
    "回答时请使用中文。"
)

# 主 Agent 据 description 判断委派,内容对齐现有 supervisor 路由说明
_DESCRIPTIONS = {
    "product": "处理商品搜索、详情、分类、评论、首页推荐等商品相关问题。",
    "order": "处理购物车、下单、支付、订单查询等订单相关问题。",
    "aftersale": "处理退换货、投诉、售后、FAQ、政策等售后相关问题。",
    "user": "处理账户、地址、登录、注册、个人信息等用户相关问题。",
    "general": "处理天气、汇率、闲聊及其他通用问题。",
}


def _make_subagent(name: str, prompt: str, tools: list[Any]) -> dict[str, Any]:
    """构造单个 SubAgent dict(含按需生成的 interrupt_on)。"""
    return {
        "name": name,
        "description": _DESCRIPTIONS[name],
        "system_prompt": prompt,
        "tools": tools,
        "interrupt_on": build_interrupt_on(tools),
    }


def build_subagents(mcp_tools: list[Any], skill_tools: list[Any]) -> list[dict[str, Any]]:
    """构建 5 个子 Agent 定义。

    Args:
        mcp_tools: 运行时注入的 MCP 工具(给 general 子 Agent)。
        skill_tools: 运行时注入的 Skill 工具(给 general 子 Agent)。

    Returns:
        SubAgent dict 列表,可直接传给 create_deep_agent(subagents=...)。
    """
    return [
        _make_subagent("product", PRODUCT_PROMPT, get_product_tools()),
        _make_subagent("order", ORDER_PROMPT, get_order_tools()),
        _make_subagent("aftersale", AFTERSALE_PROMPT, get_aftersale_tools()),
        _make_subagent("user", USER_PROMPT, get_user_tools()),
        _make_subagent(
            "general", GENERAL_PROMPT, get_general_tools(mcp_tools, skill_tools)
        ),
    ]
