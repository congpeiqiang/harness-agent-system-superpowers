"""deepagents 版对话路由 —— POST /deep/chat, /deep/chat/stream, /deep/chat/{id}/approve。

与现有 /api/v1/chat 完全并存,读取 app.state.deep_graph,复用现有 schemas 与 stream_parser。
"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from src.api.schemas import ApprovalDecision, ChatRequest, ChatResponse
from src.api.stream_parser import parse_graph_event
from src.observability.logging import get_logger
from src.observability.metrics import get_metrics

logger = get_logger("api.deep_chat")
router = APIRouter(prefix="/api/v1/deep", tags=["deep-chat"])


def _build_config(req: ChatRequest, session_id: str) -> dict:
    """构造 LangGraph configurable 配置。"""
    return {
        "configurable": {
            "thread_id": session_id,
            "user_id": req.user_id,
            "access_token": req.access_token or "",
        }
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, req: Request):
    """同步对话 —— 调用 deep_graph 并返回末条 AI 消息。"""
    graph = req.app.state.deep_graph
    session_id = body.session_id or str(uuid.uuid4())
    config = _build_config(body, session_id)

    metrics = get_metrics()
    metrics.increment_request()

    start = datetime.now(timezone.utc)
    result = await graph.ainvoke(
        {"messages": [("user", body.message)]},
        config=config,
    )

    messages = result.get("messages", [])
    last_msg = ""
    agent_name = None
    tool_calls: list[str] = []

    for msg in messages:
        role = getattr(msg, "type", "") if not isinstance(msg, tuple) else msg[0]
        if role in ("ai", "assistant"):
            content = getattr(msg, "content", "") if not isinstance(msg, tuple) else msg[1]
            last_msg = content or last_msg
            if not isinstance(msg, tuple):
                agent_name = getattr(msg, "name", None) or agent_name
            tcs = getattr(msg, "tool_calls", None)
            if tcs:
                tool_calls.extend(tc.get("name", "") for tc in tcs)
        elif role == "tool":
            name = getattr(msg, "name", "") if not isinstance(msg, tuple) else ""
            if name:
                tool_calls.append(name)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
    metrics.record_response_time(elapsed)

    return ChatResponse(
        session_id=session_id,
        message=last_msg,
        agent_name=agent_name,
        tool_calls=tool_calls,
        created_at=datetime.now(timezone.utc),
    )


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, req: Request):
    """SSE 流式对话 —— 复用现有 parse_graph_event。"""
    graph = req.app.state.deep_graph
    session_id = body.session_id or str(uuid.uuid4())
    config = _build_config(body, session_id)

    metrics = get_metrics()
    metrics.increment_request()

    async def event_generator():
        try:
            async for event in graph.astream_events(
                {"messages": [("user", body.message)]},
                config=config,
                version="v2",
            ):
                parsed = parse_graph_event(event)
                if parsed is not None:
                    yield f"event: {parsed.event}\ndata: {json.dumps({'data': parsed.data, 'agent_name': parsed.agent_name}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            logger.error("deep_stream_error", error=str(e))
            metrics.increment_error()
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/chat/{session_id}/approve")
async def approve(session_id: str, body: ApprovalDecision, req: Request):
    """人机审批恢复 —— 对 deep_graph 执行 Command(resume=...)。"""
    graph = req.app.state.deep_graph

    metrics = get_metrics()
    if body.approved:
        metrics.human_approval_count += 1
    else:
        metrics.human_rejection_count += 1

    logger.info("deep_approval_received", session_id=session_id, approved=body.approved)

    await graph.ainvoke(
        Command(resume={"approved": body.approved, "reason": body.reason or ""}),
        config={"configurable": {"thread_id": session_id}},
    )

    return {
        "session_id": session_id,
        "approved": body.approved,
        "reason": body.reason,
        "status": "processed",
    }
