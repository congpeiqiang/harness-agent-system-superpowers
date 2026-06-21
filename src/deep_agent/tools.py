"""工具收集 —— 复用现有 FecMall / RAG 工具,并合并运行时注入的 MCP / Skill 工具。

按子 Agent 职责分组返回工具列表,与现有 src/agents 下 5 个专业 Agent 一一对应。
"""
from typing import Any

from src.tools.fecmall.product_tools import (
    get_category_products,
    get_home_info,
    get_product_detail,
    get_product_reviews,
    search_products,
)
from src.tools.fecmall.cart_tools import (
    add_to_cart,
    get_cart,
    remove_cart_item,
    update_cart_item,
)
from src.tools.fecmall.order_tools import (
    get_checkout_init,
    get_order_detail,
    get_order_list,
    submit_order,
)
from src.tools.fecmall.aftersale_tools import (
    get_refund_status,
    submit_complaint,
)
from src.tools.fecmall.customer_tools import (
    add_address,
    get_address_list,
    get_user_profile,
    login,
    register,
    remove_address,
    update_profile,
)
from src.tools.rag_tools import rag_search


def get_product_tools() -> list[Any]:
    """商品子 Agent 工具(与 ProductAgent 一致,5 个)。"""
    return [
        search_products,
        get_product_detail,
        get_category_products,
        get_product_reviews,
        get_home_info,
    ]


def get_order_tools() -> list[Any]:
    """订单子 Agent 工具(与 OrderAgent 一致,8 个)。"""
    return [
        get_cart,
        add_to_cart,
        update_cart_item,
        remove_cart_item,
        get_checkout_init,
        submit_order,
        get_order_list,
        get_order_detail,
    ]


def get_aftersale_tools() -> list[Any]:
    """售后子 Agent 工具(与 AfterSaleAgent 一致,3 个,含 RAG 检索)。"""
    return [
        submit_complaint,
        get_refund_status,
        rag_search,
    ]


def get_user_tools() -> list[Any]:
    """用户子 Agent 工具(与 UserAgent 一致,7 个)。"""
    return [
        login,
        register,
        get_user_profile,
        update_profile,
        get_address_list,
        add_address,
        remove_address,
    ]


def get_general_tools(mcp_tools: list[Any], skill_tools: list[Any]) -> list[Any]:
    """通用子 Agent 工具(与 GeneralAgent 一致):运行时注入的 MCP + Skill 工具。"""
    return list(mcp_tools) + list(skill_tools)
