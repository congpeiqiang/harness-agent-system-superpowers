"""FastAPI 应用启动与健康检查集成测试"""
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_lifespan_deps():
    """Mock expensive lifespan dependencies so no real connections are made."""
    with (
        patch("src.main.MCPClientManager") as MockMCP,
        patch("src.main.SkillLoader") as MockLoader,
        patch("src.main.RAGRetriever") as MockRAG,
        patch("src.main.build_agent_graph", new_callable=AsyncMock) as mock_graph,
        patch("src.main.setup_langsmith"),
    ):
        # MCPClientManager mock
        mcp_inst = MagicMock()
        mcp_inst.connect = AsyncMock()
        mcp_inst.disconnect_all = AsyncMock()
        MockMCP.return_value = mcp_inst

        # SkillLoader mock
        loader_inst = MagicMock()
        loader_inst.load_all = AsyncMock()
        MockLoader.return_value = loader_inst

        # RAGRetriever mock
        rag_inst = MagicMock()
        rag_inst.initialize = AsyncMock()
        rag_inst.close = AsyncMock()
        MockRAG.get_instance.return_value = rag_inst

        # build_agent_graph mock
        mock_graph.return_value = MagicMock()

        yield


async def test_health_endpoint_returns_200(mock_lifespan_deps):
    """验证健康检查端点返回 200。"""
    from src.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime_seconds" in data


async def test_app_routes_registered(mock_lifespan_deps):
    """验证关键路由已注册。"""
    from src.main import app

    paths = [route.path for route in app.routes]
    assert "/api/v1/health" in paths
    assert "/api/v1/chat" in paths
    assert "/api/v1/sessions" in paths


def test_app_metadata():
    """验证应用元数据（无需 lifespan）。"""
    # Import without triggering lifespan — just check the module-level object
    from src.main import app as _app

    assert _app.title == "FecMall 智能客服系统"
    assert _app.version == "1.0.0"
