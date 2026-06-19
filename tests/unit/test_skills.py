import pytest
from src.skills.base_skill import BaseSkill
from src.skills.registry import SkillRegistry
from src.skills.builtin.currency_convert import CurrencyConvertSkill

def test_registry_register_and_list():
    registry = SkillRegistry()
    skill = CurrencyConvertSkill()
    registry.register(skill)
    skills = registry.list_skills()
    assert len(skills) == 1
    assert skills[0]["name"] == "currency_convert"

def test_registry_get_all_tools():
    registry = SkillRegistry()
    skill = CurrencyConvertSkill()
    registry.register(skill)
    tools = registry.get_all_tools()
    assert len(tools) >= 1
    assert any("convert" in t.name.lower() for t in tools)

def test_registry_unregister():
    registry = SkillRegistry()
    skill = CurrencyConvertSkill()
    registry.register(skill)
    registry.unregister("currency_convert")
    assert len(registry.list_skills()) == 0
