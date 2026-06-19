"""AfterSaleAgent — 售后投诉与退款查询专家。"""
from src.agents.base_agent import BaseAgent
from src.tools.fecmall.aftersale_tools import (
    get_refund_status,
    submit_complaint,
)
from src.tools.rag_tools import rag_search


class AfterSaleAgent(BaseAgent):
    """售后 Agent，负责投诉提交、退款查询和知识库检索。"""

    name: str = "aftersale"
    system_prompt: str = (
        "你是一个专业的电商售后助手。你可以帮助用户提交售后投诉、查询订单退款状态，"
        "以及从知识库中搜索退换货政策和常见问题。"
        "在处理投诉时请耐心倾听用户的问题，并提供清晰的解决方案。"
        "回答时请使用中文，语气友好且有同理心。"
    )

    def get_tools(self) -> list:
        """返回售后相关的 3 个工具。"""
        return [
            submit_complaint,
            get_refund_status,
            rag_search,
        ]
