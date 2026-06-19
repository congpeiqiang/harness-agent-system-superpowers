"""链路追踪"""
import uuid
from contextvars import ContextVar
import structlog

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
logger = structlog.get_logger("tracing")

class AgentTracer:
    """轻量级 Agent 调用链路追踪"""
    @staticmethod
    def start_trace() -> str:
        tid = str(uuid.uuid4())[:8]
        trace_id_var.set(tid)
        structlog.contextvars.bind_contextvars(trace_id=tid)
        return tid

    @staticmethod
    def log_step(step: str, agent: str = "", tool: str = "", **kwargs):
        logger.info("agent_trace", step=step, agent=agent, tool=tool, **kwargs)

    @staticmethod
    def end_trace():
        structlog.contextvars.unbind_contextvars("trace_id")
