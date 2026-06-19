"""BaseAgent — 所有专业 Agent 的抽象基类。

提供 invoke_node() 和 stream_node() 两个核心方法，
子类只需实现 get_tools() 即可获得完整的 Agent 执行能力。
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator

import structlog

logger = structlog.get_logger(__name__)


def _import_create_agent():
    """尝试从多个路径导入 create_agent，返回可用的工厂函数。"""
    # 尝试 1: langchain.agents (1.3.10+)
    try:
        from langchain.agents import create_agent
        return create_agent
    except ImportError:
        pass

    # 尝试 2: langgraph.prebuilt
    try:
        from langgraph.prebuilt import create_react_agent as create_agent
        return create_agent
    except ImportError:
        pass

    raise ImportError(
        "Cannot import create_agent from langchain.agents or "
        "create_react_agent from langgraph.prebuilt"
    )


def _import_command():
    """尝试导入 langgraph.types.Command。"""
    try:
        from langgraph.types import Command
        return Command
    except ImportError:
        return None


class BaseAgent(ABC):
    """所有专业 Agent 的抽象基类。

    子类必须定义:
        - name: str  — Agent 标识名称
        - system_prompt: str  — Agent 系统提示词
        - get_tools() -> list  — 返回该 Agent 可用的工具列表
    """

    name: str = ""
    system_prompt: str = ""

    def __init__(self):
        """初始化 Agent。子类如需自定义初始化可覆盖此方法。"""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define a non-empty 'name'")
        if not self.system_prompt:
            raise ValueError(
                f"{self.__class__.__name__} must define a non-empty 'system_prompt'"
            )

    @abstractmethod
    def get_tools(self) -> list:
        """返回该 Agent 可用的工具列表。子类必须实现。"""
        ...

    def _build_agent(self, model: Any, middleware: list | None = None):
        """构建 agent 实例。

        Args:
            model: LLM 模型实例 (BaseChatModel)
            middleware: 中间件列表 (可选)

        Returns:
            编译好的 agent 图 (CompiledGraph)
        """
        create_agent = _import_create_agent()
        tools = self.get_tools()

        kwargs: dict[str, Any] = {
            "model": model,
            "tools": tools,
        }

        # 尝试传入 system prompt — 不同 API 使用不同参数名
        if self.system_prompt:
            kwargs["prompt"] = self.system_prompt

        # 中间件
        if middleware:
            kwargs["middleware"] = middleware

        try:
            return create_agent(**kwargs)
        except TypeError:
            # 某些版本可能不支持 prompt/middleware 参数，降级重试
            kwargs.pop("middleware", None)
            try:
                return create_agent(**kwargs)
            except TypeError:
                kwargs.pop("prompt", None)
                return create_agent(**kwargs)

    async def invoke_node(
        self,
        state: dict[str, Any],
        *,
        model: Any,
        middleware: list | None = None,
        config: dict[str, Any] | None = None,
    ) -> Any:
        """同步调用 Agent 节点并返回 Command(goto="supervisor")。

        Args:
            state: 当前状态 (包含 messages 等)
            model: LLM 模型实例
            middleware: 中间件列表
            config: 运行时配置

        Returns:
            Command(goto="supervisor") 包含 Agent 的输出 messages
        """
        if middleware is None:
            try:
                from src.agents.middleware import build_middleware_stack
                middleware = build_middleware_stack()
            except Exception as exc:
                logger.warning("middleware_build_failed", error=str(exc))
                middleware = None

        agent = self._build_agent(model, middleware)
        result = await agent.ainvoke(state, config=config)

        Command = _import_command()
        if Command is not None:
            return Command(goto="supervisor", update=result)
        return result

    async def stream_node(
        self,
        state: dict[str, Any],
        *,
        model: Any,
        middleware: list | None = None,
        config: dict[str, Any] | None = None,
    ) -> AsyncIterator:
        """流式调用 Agent 节点，逐事件产出。

        Args:
            state: 当前状态
            model: LLM 模型实例
            middleware: 中间件列表
            config: 运行时配置

        Yields:
            Agent 执行过程中的事件
        """
        if middleware is None:
            try:
                from src.agents.middleware import build_middleware_stack
                middleware = build_middleware_stack()
            except Exception as exc:
                logger.warning("middleware_build_failed", error=str(exc))
                middleware = None

        agent = self._build_agent(model, middleware)
        async for event in agent.astream_events(state, config=config, version="v2"):
            yield event

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, tools={len(self.get_tools())})"
