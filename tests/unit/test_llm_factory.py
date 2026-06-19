"""测试多模型工厂"""
import pytest
from unittest.mock import patch, MagicMock
from src.config.llm_factory import LLMFactory


def test_create_default_model():
    """测试默认模型创建"""
    factory = LLMFactory()
    factory._instances.clear()
    llm = factory.create()
    assert llm is not None
    assert hasattr(llm, "ainvoke")


def test_create_with_agent_override():
    """测试 Agent 覆盖配置"""
    factory = LLMFactory()
    factory._instances.clear()
    llm = factory.create(agent_name="supervisor")
    assert llm is not None


def test_instance_caching():
    """测试实例缓存"""
    factory = LLMFactory()
    factory._instances.clear()
    llm1 = factory.create()
    llm2 = factory.create()
    assert llm1 is llm2
