"""FecMall 智能客服系统 — FastAPI 应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agents.graph_builder import build_agent_graph
from src.api import chat, health, sessions
from src.mcp_client_service.client.mcp_client import MCPClientManager
from src.memory.memory_manager import MemoryManager
from src.observability.langsmith_setup import setup_langsmith
from src.observability.logging import get_logger, setup_logging
from src.rag.retriever import RAGRetriever
from src.skills.loader import SkillLoader
from src.skills.registry import SkillRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise every subsystem on startup,
    tear them down gracefully on shutdown."""
    logger = get_logger("lifespan")

    # --- Observability ---------------------------------------------------
    setup_logging()
    setup_langsmith()
    logger.info("app_starting")

    # --- Memory ----------------------------------------------------------
    memory = MemoryManager("data/checkpoints.db", "data/store.db")
    app.state.memory = memory

    # --- MCP Client ------------------------------------------------------
    mcp_manager = MCPClientManager()
    try:
        await mcp_manager.connect("weather", "http://localhost:8001/sse")
    except Exception as e:
        logger.warning("mcp_connect_skipped", error=str(e))
    app.state.mcp_manager = mcp_manager

    # --- Skills ----------------------------------------------------------
    registry = SkillRegistry()
    loader = SkillLoader(registry, ["src/skills/builtin"])
    await loader.load_all()
    app.state.skill_registry = registry
    app.state.skill_loader = loader

    # --- RAG -------------------------------------------------------------
    rag = RAGRetriever.get_instance()
    try:
        await rag.initialize()
    except Exception as e:
        logger.warning("rag_init_skipped", error=str(e))
    app.state.rag = rag

    # --- Agent Graph -----------------------------------------------------
    graph = await build_agent_graph(
        memory=memory, mcp_manager=mcp_manager, skill_registry=registry
    )
    app.state.graph = graph

    logger.info("app_started")

    # ====== Ready to serve ======
    yield

    # --- Shutdown --------------------------------------------------------
    await mcp_manager.disconnect_all()
    await memory.close()
    await rag.close()
    logger.info("app_stopped")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="FecMall 智能客服系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(health.router)
