import pytest
from src.mcp_client_service.client.mcp_client import MCPClientManager

def test_mcp_client_manager_init():
    manager = MCPClientManager()
    assert manager.get_tools() == []
    assert manager.list_servers() == []
