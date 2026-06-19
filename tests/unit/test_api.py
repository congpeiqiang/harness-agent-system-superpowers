"""Tests for API route models — ChatRequest validation & HealthResponse."""
import pytest
from datetime import datetime


def test_chat_request_validation():
    """ChatRequest enforces required fields and length constraints."""
    from src.api.schemas import ChatRequest

    # Valid minimal request
    req = ChatRequest(message="hi", user_id="u1")
    assert req.message == "hi"
    assert req.user_id == "u1"
    assert req.session_id is None
    assert req.access_token is None

    # Valid full request
    req = ChatRequest(message="hello", user_id="u1", session_id="s1", access_token="tok")
    assert req.session_id == "s1"
    assert req.access_token == "tok"

    # Empty message rejected
    with pytest.raises(Exception):
        ChatRequest(message="", user_id="u1")

    # Missing user_id rejected
    with pytest.raises(Exception):
        ChatRequest(message="hi")

    # Over-length message rejected
    with pytest.raises(Exception):
        ChatRequest(message="x" * 5001, user_id="u1")


def test_health_response():
    """HealthResponse serialises with correct defaults."""
    from src.api.schemas import HealthResponse

    h = HealthResponse()
    assert h.status == "ok"
    assert h.version == "1.0.0"
    assert h.uptime_seconds == 0.0
    assert h.llm_provider == ""
    assert h.milvus_connected is False
    assert h.mcp_servers == []
    assert h.active_skills == 0

    # Custom values
    h2 = HealthResponse(
        status="degraded",
        version="2.0.0",
        uptime_seconds=123.4,
        llm_provider="deepseek",
        milvus_connected=True,
        mcp_servers=["weather"],
        active_skills=3,
    )
    assert h2.status == "degraded"
    assert h2.active_skills == 3
    assert h2.mcp_servers == ["weather"]
