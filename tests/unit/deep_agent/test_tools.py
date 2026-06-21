"""deep_agent 工具收集模块测试。"""
from src.deep_agent.tools import (
    get_product_tools,
    get_order_tools,
    get_aftersale_tools,
    get_user_tools,
    get_general_tools,
)


def test_product_tools_count_and_names():
    tools = get_product_tools()
    names = {t.name for t in tools}
    assert len(tools) == 5
    assert names == {
        "search_products",
        "get_product_detail",
        "get_category_products",
        "get_product_reviews",
        "get_home_info",
    }


def test_order_tools_count():
    assert len(get_order_tools()) == 8


def test_aftersale_tools_include_rag():
    names = {t.name for t in get_aftersale_tools()}
    assert len(names) == 3
    assert "rag_search" in names


def test_user_tools_count():
    assert len(get_user_tools()) == 7


def test_general_tools_merges_injected():
    fake_mcp = ["MCP_TOOL"]
    fake_skill = ["SKILL_TOOL"]
    tools = get_general_tools(fake_mcp, fake_skill)
    assert "MCP_TOOL" in tools and "SKILL_TOOL" in tools
