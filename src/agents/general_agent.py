"""GeneralAgent — 通用 Agent，接收外部注入的 MCP/Skill 工具。"""
from typing import Any

from src.agents.base_agent import BaseAgent


class GeneralAgent(BaseAgent):
    """通用 Agent，无内置工具，通过 extra_tools 注入 MCP 和 Skill 工具。"""

    name: str = "general"
    system_prompt: str = (
        "你是一个通用的智能助手。你可以使用各种外部工具来帮助用户完成任务，"
        "包括天气查询、货币转换等功能。"
        "请根据用户的需求选择合适的工具，并提供准确的信息。"
        "回答时请使用中文。"
    )

    def __init__(self, extra_tools: list[Any] | None = None):
        """初始化通用 Agent。

        Args:
            extra_tools: 外部注入的工具列表（如 MCP 工具、Skill 工具）
        """
        self._extra_tools = extra_tools or []
        super().__init__()

    def get_tools(self) -> list:
        """返回注入的外部工具列表。"""
        return list(self._extra_tools)
