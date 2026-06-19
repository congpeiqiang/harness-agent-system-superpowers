"""Skill 注册表"""
from .base_skill import BaseSkill
from langchain_core.tools import BaseTool
from src.observability.logging import get_logger

logger = get_logger("skill_registry")

class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        self._skills[skill.name] = skill
        logger.info("skill_registered", name=skill.name, version=skill.version)

    def unregister(self, name: str):
        self._skills.pop(name, None)

    def get_all_tools(self) -> list[BaseTool]:
        tools = []
        for skill in self._skills.values():
            tools.extend(skill.get_tools())
        return tools

    def list_skills(self) -> list[dict]:
        return [{"name": s.name, "description": s.description, "version": s.version, "tool_count": len(s.get_tools())} for s in self._skills.values()]
