"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    user_id: str = Field(...)
    access_token: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    agent_name: Optional[str] = None
    tool_calls: list[str] = []
    created_at: datetime


class StreamEvent(BaseModel):
    event: str
    data: str
    agent_name: Optional[str] = None


class ApprovalDecision(BaseModel):
    approved: bool
    reason: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    uptime_seconds: float = 0.0
    llm_provider: str = ""
    milvus_connected: bool = False
    mcp_servers: list[str] = []
    active_skills: int = 0
