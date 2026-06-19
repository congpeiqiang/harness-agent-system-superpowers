"""Skill 插件基类"""
from abc import ABC, abstractmethod
from langchain_core.tools import BaseTool

class BaseSkill(ABC):
    """所有 Skill 插件的基类"""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def get_tools(self) -> list[BaseTool]:
        """返回该 Skill 提供的工具列表"""
        ...

    async def on_load(self):
        pass

    async def on_unload(self):
        pass
