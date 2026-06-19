"""Tests for Pydantic schemas and SSE stream parser."""
import pytest
from datetime import datetime


def test_chat_request_validation():
    """ChatRequest should validate fields and enforce constraints."""
    from src.api.schemas import ChatRequest

    # Valid request
    req = ChatRequest(message="hello", user_id="u1", session_id="s1")
    assert req.message == "hello"
    assert req.user_id == "u1"
    assert req.session_id == "s1"
    assert req.access_token is None

    # Empty message should fail
    with pytest.raises(Exception):
        ChatRequest(message="", user_id="u1")

    # Missing user_id should fail
    with pytest.raises(Exception):
        ChatRequest(message="hello")


def test_stream_event_and_parser():
    """StreamEvent model works and parse_graph_event converts known event types."""
    from src.api.schemas import StreamEvent
    from src.api.stream_parser import parse_graph_event

    # Direct model construction
    evt = StreamEvent(event="token", data="hi", agent_name="coder")
    assert evt.event == "token"
    assert evt.data == "hi"

    # on_chat_model_stream → token
    result = parse_graph_event({
        "event": "on_chat_model_stream",
        "data": {"chunk": type("Chunk", (), {"content": "Hello"})()},
    })
    assert result is not None
    assert result.event == "token"
    assert result.data == "Hello"

    # on_tool_start → tool_start
    result = parse_graph_event({
        "event": "on_tool_start",
        "name": "search_web",
        "data": {"input": {"query": "test"}},
    })
    assert result is not None
    assert result.event == "tool_start"
    assert result.data == "search_web"

    # on_tool_end → tool_end
    result = parse_graph_event({
        "event": "on_tool_end",
        "name": "search_web",
        "data": {"output": "result text"},
    })
    assert result is not None
    assert result.event == "tool_end"

    # on_chain_start with supervisor → agent_switch
    result = parse_graph_event({
        "event": "on_chain_start",
        "name": "supervisor",
        "data": {"input": {"next_agent": "coder"}},
    })
    assert result is not None
    assert result.event == "agent_switch"

    # Unknown event → None
    result = parse_graph_event({
        "event": "on_chat_model_start",
        "data": {},
    })
    assert result is None
