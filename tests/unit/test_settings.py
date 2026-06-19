import os
import pytest
from src.config.settings import get_settings, Settings

def test_settings_loads_defaults():
    settings = Settings()
    assert settings.llm.default_provider == "deepseek"
    assert settings.fecmall.default_currency == "USD"
    assert settings.middleware.tool_call_limit.run_limit == 15

def test_settings_env_override():
    os.environ["FECMALL_BASE_URL"] = "http://test-server/appserver"
    settings = Settings()
    assert settings.fecmall.base_url == "http://test-server/appserver"
    del os.environ["FECMALL_BASE_URL"]

def test_get_settings_singleton():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
