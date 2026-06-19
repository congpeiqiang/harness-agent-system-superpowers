"""OrderAgent — 购物车与订单管理专家。"""
from src.agents.base_agent import BaseAgent
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


class OrderAgent(BaseAgent):
    """订单 Agent，负责购物车管理和订单全流程。"""

    name: str = "order"
    system_prompt: str = (
        "你是一个专业的电商订单助手。你可以帮助用户管理购物车（添加、修改、删除商品）、"
        "查看购物车内容、初始化结算、提交订单、查看订单列表和订单详情。"
        "请在执行敏感操作（如提交订单、删除商品）前向用户确认。"
        "回答时请使用中文，并对订单信息做出清晰的总结。"
    )

    def get_tools(self) -> list:
        """返回购物车 + 订单相关的 8 个工具。"""
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
