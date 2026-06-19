"""Skill 加载器"""
import importlib.util
import inspect
from pathlib import Path
from .base_skill import BaseSkill
from .registry import SkillRegistry
from src.observability.logging import get_logger

logger = get_logger("skill_loader")

class SkillLoader:
    def __init__(self, registry: SkillRegistry, skill_dirs: list[str]):
        self.registry = registry
        self.skill_dirs = [Path(d) for d in skill_dirs]

    async def load_all(self):
        for skill_dir in self.skill_dirs:
            if not skill_dir.exists():
                continue
            for py_file in sorted(skill_dir.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                await self._load_module(py_file)

    async def _load_module(self, path: Path):
        try:
            module_name = f"skills.dynamic.{path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if not spec or not spec.loader:
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name, cls in inspect.getmembers(module, inspect.isclass):
                if issubclass(cls, BaseSkill) and cls is not BaseSkill:
                    instance = cls()
                    await instance.on_load()
                    self.registry.register(instance)
        except Exception as e:
            logger.error("skill_load_failed", path=str(path), error=str(e))

    async def reload_all(self):
        for skill_info in self.registry.list_skills():
            skill = self.registry._skills.get(skill_info["name"])
            if skill:
                await skill.on_unload()
            self.registry.unregister(skill_info["name"])
        await self.load_all()
        logger.info("skills_reloaded", count=len(self.registry.list_skills()))
