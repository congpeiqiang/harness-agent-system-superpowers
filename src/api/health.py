"""系统路由 — /health, /metrics, /skills, /skills/reload"""
import time

from fastapi import APIRouter, Request

from src.api.schemas import HealthResponse
from src.observability.logging import get_logger
from src.observability.metrics import get_metrics

logger = get_logger("api.health")
router = APIRouter(prefix="/api/v1", tags=["system"])

_start_time = time.monotonic()


@router.get("/health", response_model=HealthResponse)
async def health(req: Request):
    """Health check endpoint."""
    uptime = time.monotonic() - _start_time

    # Gather info from app state
    mcp_servers: list[str] = []
    active_skills = 0
    llm_provider = ""
    milvus_connected = False

    if hasattr(req.app.state, "mcp"):
        mcp_manager = req.app.state.mcp
        if hasattr(mcp_manager, "get_server_names"):
            mcp_servers = mcp_manager.get_server_names()

    if hasattr(req.app.state, "skill_registry"):
        registry = req.app.state.skill_registry
        if hasattr(registry, "list_skills"):
            active_skills = len(registry.list_skills())

    if hasattr(req.app.state, "settings"):
        settings = req.app.state.settings
        if hasattr(settings, "llm"):
            llm_provider = settings.llm.default_provider

    return HealthResponse(
        status="ok",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        llm_provider=llm_provider,
        milvus_connected=milvus_connected,
        mcp_servers=mcp_servers,
        active_skills=active_skills,
    )


@router.get("/metrics")
async def metrics():
    """Return agent runtime metrics."""
    return get_metrics().to_dict()


@router.get("/skills")
async def list_skills(req: Request):
    """List all loaded skills."""
    if hasattr(req.app.state, "skill_registry"):
        return req.app.state.skill_registry.list_skills()
    return []


@router.post("/skills/reload")
async def reload_skills(req: Request):
    """Reload all skills from disk."""
    if hasattr(req.app.state, "skill_loader"):
        loader = req.app.state.skill_loader
        await loader.reload_all()
        count = len(req.app.state.skill_registry.list_skills())
        logger.info("skills_reloaded_via_api", count=count)
        return {"status": "reloaded", "count": count}
    return {"status": "no_loader_available", "count": 0}
