"""MCP 客户端管理器 — 管理多个 MCP Server 连接"""
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.sse import sse_client
from src.observability.logging import get_logger

logger = get_logger("mcp_client")

class MCPClientManager:
    """管理多个 MCP Server 连接的生命周期，聚合所有 MCP 工具"""
    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._tools: list = []
        self._connections: list = []

    async def connect(self, server_name: str, sse_url: str):
        """连接一个 MCP Server 并加载其工具"""
        try:
            conn = sse_client(sse_url)
            read_stream, write_stream = await conn.__aenter__()
            self._connections.append(conn)
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            await session.initialize()
            self._sessions[server_name] = session
            tools = await load_mcp_tools(session)
            self._tools.extend(tools)
            logger.info("mcp_connected", server=server_name, tools=len(tools))
        except Exception as e:
            logger.error("mcp_connect_failed", server=server_name, error=str(e))

    def get_tools(self) -> list:
        return self._tools

    def list_servers(self) -> list[str]:
        return list(self._sessions.keys())

    async def disconnect_all(self):
        for server_name, session in self._sessions.items():
            try:
                await session.__aexit__(None, None, None)
            except Exception as e:
                logger.warning("mcp_disconnect_error", server=server_name, error=str(e))
        for conn in self._connections:
            try:
                await conn.__aexit__(None, None, None)
            except Exception:
                pass
        self._sessions.clear()
        self._tools.clear()
        self._connections.clear()
