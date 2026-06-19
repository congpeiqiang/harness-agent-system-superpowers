"""LangSmith 可观测性初始化"""
import os
from src.config.settings import get_settings
from src.observability.logging import get_logger

logger = get_logger("langsmith")

def setup_langsmith():
    """初始化 LangSmith 追踪。设置环境变量后，LangChain/LangGraph 自动追踪。"""
    settings = get_settings()
    if not settings.observability.langsmith.enabled:
        logger.info("langsmith_disabled", reason="配置中已禁用")
        return
    os.environ["LANGSMITH_TRACING"] = "true"
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    else:
        logger.warning("langsmith_no_api_key", reason="LANGSMITH_API_KEY not set")
    os.environ["LANGSMITH_PROJECT"] = settings.observability.langsmith.project
    logger.info("langsmith_initialized", project=settings.observability.langsmith.project)
