"""Tests for FecMall product tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.runnables import RunnableConfig

from src.tools.fecmall.product_tools import (
    search_products,
    get_product_detail,
    get_category_products,
    get_product_reviews,
    get_home_info,
)


def _make_config(token: str = "test-token") -> RunnableConfig:
    return {"configurable": {"access_token": token}}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = str(json_data)
    return resp


@pytest.mark.asyncio
@patch("src.tools.fecmall.product_tools.FecMallClient")
async def test_search_products(mock_client_cls):
    """search_products returns formatted product list."""
    mock_http = AsyncMock()
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_http
    mock_client_instance.__aexit__.return_value = False
    mock_client_cls.return_value = mock_client_instance

    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "products": [
                {"name": "Test Product", "price": "$10.00", "sku": "SKU001"},
            ],
            "count": 1,
        },
    })

    result = await search_products.ainvoke(
        {"keyword": "test", "page": 1, "config": _make_config()}
    )

    assert "Test Product" in result
    assert "SKU001" in result
    mock_http.get.assert_awaited_once()
    call_args = mock_http.get.call_args
    assert "catalogsearch" in call_args.args[0] or "catalogsearch" in str(call_args)


@pytest.mark.asyncio
@patch("src.tools.fecmall.product_tools.FecMallClient")
async def test_get_product_detail(mock_client_cls):
    """get_product_detail returns formatted product info."""
    mock_http = AsyncMock()
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_http
    mock_client_instance.__aexit__.return_value = False
    mock_client_cls.return_value = mock_client_instance

    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "name": "Detail Product",
            "price": "$25.00",
            "sku": "SKU002",
            "description": "A great product",
        },
    })

    result = await get_product_detail.ainvoke(
        {"product_id": "123", "config": _make_config()}
    )

    assert "Detail Product" in result
    assert "SKU002" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.product_tools.FecMallClient")
async def test_search_products_error_handling(mock_client_cls):
    """search_products returns error string on failure, never raises."""
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.side_effect = Exception("Connection failed")
    mock_client_cls.return_value = mock_client_instance

    result = await search_products.ainvoke(
        {"keyword": "test", "config": _make_config()}
    )

    assert "error" in result.lower() or "Error" in result or "错误" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.product_tools.FecMallClient")
async def test_get_category_products(mock_client_cls):
    """get_category_products returns formatted product list."""
    mock_http = AsyncMock()
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_http
    mock_client_instance.__aexit__.return_value = False
    mock_client_cls.return_value = mock_client_instance

    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "products": [
                {"name": "Cat Product", "price": "$15.00", "sku": "SKU003"},
            ],
        },
    })

    result = await get_category_products.ainvoke(
        {"category_id": "5", "config": _make_config()}
    )

    assert "Cat Product" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.product_tools.FecMallClient")
async def test_get_product_reviews(mock_client_cls):
    """get_product_reviews returns formatted review list."""
    mock_http = AsyncMock()
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_http
    mock_client_instance.__aexit__.return_value = False
    mock_client_cls.return_value = mock_client_instance

    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "reviews": [
                {"user": "Alice", "content": "Great!", "rating": 5},
            ],
        },
    })

    result = await get_product_reviews.ainvoke(
        {"product_id": "123", "config": _make_config()}
    )

    assert "Alice" in result or "Great" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.product_tools.FecMallClient")
async def test_get_home_info(mock_client_cls):
    """get_home_info returns formatted home page data."""
    mock_http = AsyncMock()
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_http
    mock_client_instance.__aexit__.return_value = False
    mock_client_cls.return_value = mock_client_instance

    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "banner": [{"img": "banner.jpg"}],
            "bestSeller": [{"name": "Best Product"}],
        },
    })

    result = await get_home_info.ainvoke({"config": _make_config()})

    assert "Best Product" in result or "banner" in result.lower()
