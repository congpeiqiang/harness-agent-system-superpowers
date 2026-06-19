import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from src.tools.fecmall.client import FecMallClient

@pytest.mark.asyncio
async def test_client_context_manager():
    """测试异步上下文管理器"""
    client = FecMallClient(access_token="test-token")
    async with client as http:
        assert isinstance(http, httpx.AsyncClient)
        assert http.headers["access-token"] == "test-token"
        assert "fecshop-currency" in http.headers

@pytest.mark.asyncio
async def test_client_default_headers():
    """测试默认请求头"""
    client = FecMallClient()
    async with client as http:
        assert "access-token" not in http.headers
        assert http.headers["fecshop-currency"] == "USD"
        assert http.headers["fecshop-lang"] == "en_US"
