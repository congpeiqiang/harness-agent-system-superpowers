"""ProductAgent — 商品查询与浏览专家。"""
from src.agents.base_agent import BaseAgent
from src.tools.fecmall.product_tools import (
    get_category_products,
    get_home_info,
    get_product_detail,
    get_product_reviews,
    search_products,
)


class ProductAgent(BaseAgent):
    """商品 Agent，负责商品搜索、详情、分类、评论、首页信息。"""

    name: str = "product"
    system_prompt: str = (
        "你是一个专业的电商商品助手。你可以帮助用户搜索商品、查看商品详情、"
        "浏览分类商品、阅读商品评论以及获取首页推荐信息。"
        "请根据用户的需求，使用合适的工具为他们提供准确的商品信息。"
        "回答时请使用中文，并对商品信息做出清晰的总结和推荐。"
    )

    def get_tools(self) -> list:
        """返回商品相关的 5 个工具。"""
        return [
            search_products,
            get_product_detail,
            get_category_products,
            get_product_reviews,
            get_home_info,
        ]
