"""结构化日志模块"""
import logging
import structlog

def setup_logging(level: str = "INFO"):
    """初始化 structlog 结构化日志"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )

def get_logger(name: str = ""):
    """获取结构化日志器"""
    return structlog.get_logger(name)
