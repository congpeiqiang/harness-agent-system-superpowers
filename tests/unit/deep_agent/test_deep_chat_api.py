"""deep_chat 路由测试 —— mock deep_graph,验证同步对话端点。"""
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from src.api import deep_chat


class _FakeGraph:
    async def ainvoke(self, payload, config):
        return {"messages": [HumanMessage(content="你好"), AIMessage(content="您好,有什么可以帮您?")]}


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(deep_chat.router)
    app.state.deep_graph = _FakeGraph()
    return TestClient(app)


def test_deep_chat_returns_last_ai_message(client):
    resp = client.post(
        "/api/v1/deep/chat",
        json={"message": "你好", "user_id": "u1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "您好,有什么可以帮您?"
    assert body["session_id"]


def test_deep_chat_prefix_isolated_from_existing():
    # 路由前缀必须是 /api/v1/deep,避免与现有 /api/v1/chat 冲突
    assert deep_chat.router.prefix == "/api/v1/deep"
