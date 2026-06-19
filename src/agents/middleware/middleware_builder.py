"""中间件栈构建器 — 按顺序组装 7+1 个中间件"""
from typing import Any

import structlog

from src.agents.middleware.custom_pii import ChinaPIIMiddleware
from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

# 尝试从多个可能的路径导入 langchain 中间件
_IMPORT_WARNINGS: list[str] = []


def _import_middlewares() -> dict[str, type]:
    """尝试从多个路径导入中间件类，返回成功导入的类字典。"""
    middleware_classes = {}
    target_names = [
        "ModelRetryMiddleware",
        "ModelFallbackMiddleware",
        "SummarizationMiddleware",
        "PIIMiddleware",
        "HumanInTheLoopMiddleware",
        "ToolRetryMiddleware",
        "ToolCallLimitMiddleware",
    ]

    # 尝试路径 1: langchain.agents.middleware
    try:
        import langchain.agents.middleware as mw
        for name in target_names:
            cls = getattr(mw, name, None)
            if cls is not None:
                middleware_classes[name] = cls
        if middleware_classes:
            return middleware_classes
    except ImportError:
        pass

    # 尝试路径 2: langgraph.prebuilt.middleware
    try:
        import langgraph.prebuilt.middleware as mw
        for name in target_names:
            cls = getattr(mw, name, None)
            if cls is not None:
                middleware_classes[name] = cls
        if middleware_classes:
            _IMPORT_WARNINGS.append(
                "langchain.agents.middleware unavailable; using langgraph.prebuilt.middleware"
            )
            return middleware_classes
    except ImportError:
        pass

    _IMPORT_WARNINGS.append(
        "No middleware module found; only ChinaPIIMiddleware will be available"
    )
    return middleware_classes


def build_middleware_stack(
    *,
    fallback_models: list[str] | None = None,
    summarization_model: Any | None = None,
) -> list:
    """构建并返回有序中间件栈。

    中间件按以下顺序组装：
    1. ModelRetryMiddleware   — 模型调用失败自动重试
    2. ModelFallbackMiddleware — 主模型不可用时降级到备用模型
    3. SummarizationMiddleware — 超长上下文自动摘要
    4. PIIMiddleware           — 通用 PII 检测 (email/credit_card 等)
    5. ChinaPIIMiddleware      — 中国手机号/身份证/银行卡脱敏
    6. HumanInTheLoopMiddleware — 人工审批 (可选)
    7. ToolRetryMiddleware     — 工具调用失败重试
    8. ToolCallLimitMiddleware — 工具调用次数限制

    Args:
        fallback_models: 备用模型列表，用于 ModelFallbackMiddleware。
            若为空或未提供，则跳过该中间件。
        summarization_model: 用于摘要的模型 (BaseChatModel 或 model 字符串)。
            若为 None，使用默认字符串 "gpt-4o-mini"。

    Returns:
        按顺序排列的中间件实例列表。
    """
    settings = get_settings()
    mw_cfg = settings.middleware

    # 导入所有可用的中间件类
    mw_classes = _import_middlewares()

    # 记录导入警告
    for warn in _IMPORT_WARNINGS:
        logger.warning("middleware_import_fallback", message=warn)

    stack: list = []

    # 1. ModelRetryMiddleware
    if "ModelRetryMiddleware" in mw_classes:
        stack.append(mw_classes["ModelRetryMiddleware"](
            max_retries=mw_cfg.model_retry.max_retries,
            initial_delay=mw_cfg.model_retry.retry_delay,
            backoff_factor=mw_cfg.model_retry.retry_delay,
        ))
        logger.debug("middleware_added", name="ModelRetryMiddleware")

    # 2. ModelFallbackMiddleware (仅当有备用模型时)
    if fallback_models and "ModelFallbackMiddleware" in mw_classes:
        stack.append(mw_classes["ModelFallbackMiddleware"](
            fallback_models[0], *fallback_models[1:]
        ))
        logger.debug("middleware_added", name="ModelFallbackMiddleware")

    # 3. SummarizationMiddleware
    if "SummarizationMiddleware" in mw_classes:
        model = summarization_model or "gpt-4o-mini"
        stack.append(mw_classes["SummarizationMiddleware"](
            model=model,
            trim_tokens_to_summarize=mw_cfg.summarization.max_tokens,
            keep=("messages", mw_cfg.summarization.keep_messages),
        ))
        logger.debug("middleware_added", name="SummarizationMiddleware")

    # 4. PIIMiddleware (通用 PII — email/credit_card)
    if "PIIMiddleware" in mw_classes:
        # 添加 email 和信用卡检测
        stack.append(mw_classes["PIIMiddleware"](
            "email", strategy="redact", apply_to_input=True, apply_to_output=True,
        ))
        stack.append(mw_classes["PIIMiddleware"](
            "credit_card", strategy="mask", apply_to_input=True, apply_to_output=True,
        ))
        logger.debug("middleware_added", name="PIIMiddleware (email + credit_card)")

    # 5. ChinaPIIMiddleware (中国特有 PII)
    stack.append(ChinaPIIMiddleware())
    logger.debug("middleware_added", name="ChinaPIIMiddleware")

    # 6. HumanInTheLoopMiddleware (可选)
    if mw_cfg.human_in_the_loop.enabled and "HumanInTheLoopMiddleware" in mw_classes:
        # 为所有工具启用审批，或使用指定工具列表
        approve_tools = mw_cfg.human_in_the_loop.approve_tool_names
        interrupt_on = {tool: True for tool in approve_tools} if approve_tools else {}
        if interrupt_on:
            stack.append(mw_classes["HumanInTheLoopMiddleware"](
                interrupt_on=interrupt_on,
            ))
            logger.debug("middleware_added", name="HumanInTheLoopMiddleware")

    # 7. ToolRetryMiddleware
    if "ToolRetryMiddleware" in mw_classes:
        stack.append(mw_classes["ToolRetryMiddleware"](
            max_retries=mw_cfg.tool_retry.max_retries,
            backoff_factor=mw_cfg.tool_retry.backoff_factor,
        ))
        logger.debug("middleware_added", name="ToolRetryMiddleware")

    # 8. ToolCallLimitMiddleware
    if "ToolCallLimitMiddleware" in mw_classes:
        stack.append(mw_classes["ToolCallLimitMiddleware"](
            run_limit=mw_cfg.tool_call_limit.run_limit,
            thread_limit=mw_cfg.tool_call_limit.thread_limit,
        ))
        logger.debug("middleware_added", name="ToolCallLimitMiddleware")

    logger.info("middleware_stack_built", count=len(stack))
    return stack
