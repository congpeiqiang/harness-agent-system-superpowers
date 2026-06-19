"""SSE stream parser — converts LangGraph astream_events to StreamEvent."""
from typing import Optional
from src.api.schemas import StreamEvent


def parse_graph_event(event: dict) -> Optional[StreamEvent]:
    """Parse a LangGraph astream_event dict into a StreamEvent.

    Mappings:
        on_chat_model_stream → "token"
        on_tool_start        → "tool_start"
        on_tool_end          → "tool_end"
        on_chain_start (supervisor) → "agent_switch"

    Returns None for unrecognized event types.
    """
    event_type = event.get("event", "")
    data = event.get("data", {})
    name = event.get("name", "")

    if event_type == "on_chat_model_stream":
        chunk = data.get("chunk")
        content = ""
        if chunk is not None:
            content = getattr(chunk, "content", "") or ""
        return StreamEvent(event="token", data=content)

    if event_type == "on_tool_start":
        return StreamEvent(event="tool_start", data=name)

    if event_type == "on_tool_end":
        output = data.get("output", "")
        return StreamEvent(event="tool_end", data=name, agent_name=str(output) if output else None)

    if event_type == "on_chain_start" and name == "supervisor":
        inp = data.get("input", {})
        next_agent = inp.get("next_agent", "") if isinstance(inp, dict) else ""
        return StreamEvent(event="agent_switch", data=next_agent)

    return None
