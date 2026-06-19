"""会话管理路由 — POST/GET/DELETE /sessions"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from src.api.schemas import SessionInfo
from src.observability.logging import get_logger

logger = get_logger("api.sessions")
router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.get("/sessions")
async def list_sessions(user_id: str):
    """List sessions for a user. Placeholder — full impl needs checkpointer.alist()."""
    return {"sessions": [], "user_id": user_id}


@router.post("/sessions", response_model=SessionInfo)
async def create_session(body: dict, req: Request):
    """Create a new session and return SessionInfo."""
    user_id = body.get("user_id", "")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    logger.info("session_created", session_id=session_id, user_id=user_id)

    return SessionInfo(
        session_id=session_id,
        user_id=user_id,
        message_count=0,
        created_at=now,
        updated_at=now,
    )


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, req: Request):
    """Retrieve session history from the checkpointer."""
    memory = req.app.state.memory
    try:
        checkpointer = await memory.get_checkpointer()
        # Retrieve checkpoint tuple for the thread
        checkpoint_tuple = await checkpointer.aget(
            {"configurable": {"thread_id": session_id}}
        )
        if checkpoint_tuple is None:
            raise HTTPException(status_code=404, detail="session not found")

        checkpoint = checkpoint_tuple
        # Extract messages from checkpoint metadata if available
        channel_values = getattr(checkpoint, "channel_values", {})
        messages = channel_values.get("messages", [])

        return {
            "session_id": session_id,
            "messages": [
                {
                    "role": getattr(m, "type", "unknown"),
                    "content": getattr(m, "content", str(m)),
                }
                for m in messages
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("history_fetch_failed", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="failed to fetch history")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, req: Request):
    """Delete a session."""
    logger.info("session_deleted", session_id=session_id)
    return {"session_id": session_id, "status": "deleted"}
