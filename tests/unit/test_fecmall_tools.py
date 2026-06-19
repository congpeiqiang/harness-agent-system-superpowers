"""Tests for FecMall cart, order, customer, and aftersale tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.runnables import RunnableConfig


def _make_config(token: str = "test-token") -> RunnableConfig:
    return {"configurable": {"access_token": token}}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = str(json_data)
    return resp


def _setup_mock_client(mock_client_cls, mock_http=None):
    """Helper to set up a mock FecMallClient with standard async context manager."""
    if mock_http is None:
        mock_http = AsyncMock()
    mock_client_instance = AsyncMock()
    mock_client_instance.__aenter__.return_value = mock_http
    mock_client_instance.__aexit__.return_value = False
    mock_client_cls.return_value = mock_client_instance
    return mock_http


# ──────────────────────────────────────────────────────────────────────────────
# Cart tools
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
@patch("src.tools.fecmall.cart_tools.FecMallClient")
async def test_get_cart(mock_client_cls):
    """get_cart returns formatted cart data."""
    from src.tools.fecmall.cart_tools import get_cart
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "products": [
                {"name": "Cart Item", "qty": 2, "price": "$10.00"},
            ],
            "total": "$20.00",
        },
    })

    result = await get_cart.ainvoke({"config": _make_config()})

    assert "Cart Item" in result
    assert "$20.00" in result
    mock_http.get.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.tools.fecmall.cart_tools.FecMallClient")
async def test_add_to_cart(mock_client_cls):
    """add_to_cart posts product and returns success info."""
    from src.tools.fecmall.cart_tools import add_to_cart
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"message": "added", "cart_qty": 3},
    })

    result = await add_to_cart.ainvoke(
        {"product_id": "100", "qty": 2, "config": _make_config()}
    )

    assert "added" in result.lower() or "200" in result or "成功" in result
    mock_http.post.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.tools.fecmall.cart_tools.FecMallClient")
async def test_update_cart_item(mock_client_cls):
    """update_cart_item posts updated qty."""
    from src.tools.fecmall.cart_tools import update_cart_item
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"message": "updated"},
    })

    result = await update_cart_item.ainvoke(
        {"item_id": "item-1", "qty": 5, "config": _make_config()}
    )

    assert "updated" in result.lower() or "200" in result or "成功" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.cart_tools.FecMallClient")
async def test_remove_cart_item(mock_client_cls):
    """remove_cart_item calls update with qty=0."""
    from src.tools.fecmall.cart_tools import remove_cart_item
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"message": "removed"},
    })

    result = await remove_cart_item.ainvoke(
        {"item_id": "item-1", "config": _make_config()}
    )

    assert "removed" in result.lower() or "200" in result or "成功" in result or "删除" in result


# ──────────────────────────────────────────────────────────────────────────────
# Order tools
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
@patch("src.tools.fecmall.order_tools.FecMallClient")
async def test_get_checkout_init(mock_client_cls):
    """get_checkout_init returns checkout init data."""
    from src.tools.fecmall.order_tools import get_checkout_init
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {"address_list": [], "payment_methods": [], "shipping_methods": []},
    })

    result = await get_checkout_init.ainvoke({"config": _make_config()})

    assert "address_list" in result or "payment" in result
    mock_http.get.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.tools.fecmall.order_tools.FecMallClient")
async def test_submit_order(mock_client_cls):
    """submit_order posts order data and returns order confirmation."""
    from src.tools.fecmall.order_tools import submit_order
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"increment_id": "100000001", "message": "order placed"},
    })

    result = await submit_order.ainvoke({
        "address_id": "addr-1",
        "payment_method": "checkmo",
        "shipping_method": "flatrate_flatrate",
        "config": _make_config(),
    })

    assert "100000001" in result or "order" in result.lower() or "成功" in result
    mock_http.post.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.tools.fecmall.order_tools.FecMallClient")
async def test_get_order_list(mock_client_cls):
    """get_order_list returns formatted order list."""
    from src.tools.fecmall.order_tools import get_order_list
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "orders": [
                {"increment_id": "100000001", "status": "pending", "total": "$50.00"},
            ],
            "count": 1,
        },
    })

    result = await get_order_list.ainvoke({"page": 1, "config": _make_config()})

    assert "100000001" in result
    mock_http.get.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.tools.fecmall.order_tools.FecMallClient")
async def test_get_order_detail(mock_client_cls):
    """get_order_detail returns formatted order info."""
    from src.tools.fecmall.order_tools import get_order_detail
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "increment_id": "100000001",
            "status": "processing",
            "items": [{"name": "Item A", "qty": 1}],
        },
    })

    result = await get_order_detail.ainvoke(
        {"order_id": "100000001", "config": _make_config()}
    )

    assert "100000001" in result
    assert "Item A" in result


# ──────────────────────────────────────────────────────────────────────────────
# Customer tools
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_login(mock_client_cls):
    """login posts credentials and returns access token info."""
    from src.tools.fecmall.customer_tools import login
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"access_token": "new-token-123", "name": "Alice"},
    })

    result = await login.ainvoke({
        "email": "alice@example.com",
        "password": "secret",
    })

    assert "new-token-123" in result or "Alice" in result or "成功" in result
    mock_http.post.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_register(mock_client_cls):
    """register posts new user data and returns success info."""
    from src.tools.fecmall.customer_tools import register
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"access_token": "reg-token", "message": "registered"},
    })

    result = await register.ainvoke({
        "email": "bob@example.com",
        "password": "secret",
        "firstname": "Bob",
        "lastname": "Smith",
    })

    assert "reg-token" in result or "registered" in result.lower() or "成功" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_get_user_profile(mock_client_cls):
    """get_user_profile returns formatted user info."""
    from src.tools.fecmall.customer_tools import get_user_profile
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {"firstname": "Alice", "lastname": "Smith", "email": "alice@example.com"},
    })

    result = await get_user_profile.ainvoke({"config": _make_config()})

    assert "Alice" in result
    assert "alice@example.com" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_update_profile(mock_client_cls):
    """update_profile posts updated fields."""
    from src.tools.fecmall.customer_tools import update_profile
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"message": "updated"},
    })

    result = await update_profile.ainvoke({
        "firstname": "Alice",
        "lastname": "Jones",
        "config": _make_config(),
    })

    assert "updated" in result.lower() or "成功" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_get_address_list(mock_client_cls):
    """get_address_list returns formatted address list."""
    from src.tools.fecmall.customer_tools import get_address_list
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "addresses": [
                {"id": "addr-1", "firstname": "Alice", "city": "NY"},
            ],
        },
    })

    result = await get_address_list.ainvoke({"config": _make_config()})

    assert "addr-1" in result or "Alice" in result or "NY" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_add_address(mock_client_cls):
    """add_address posts new address data."""
    from src.tools.fecmall.customer_tools import add_address
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"message": "saved", "address_id": "addr-2"},
    })

    result = await add_address.ainvoke({
        "firstname": "Alice",
        "lastname": "Smith",
        "street": "123 Main St",
        "city": "NY",
        "country": "US",
        "telephone": "555-0001",
        "config": _make_config(),
    })

    assert "saved" in result.lower() or "addr-2" in result or "成功" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.customer_tools.FecMallClient")
async def test_remove_address(mock_client_cls):
    """remove_address posts delete request."""
    from src.tools.fecmall.customer_tools import remove_address
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.post.return_value = _mock_response({
        "code": 200,
        "data": {"message": "removed"},
    })

    result = await remove_address.ainvoke(
        {"address_id": "addr-1", "config": _make_config()}
    )

    assert "removed" in result.lower() or "成功" in result or "删除" in result


# ──────────────────────────────────────────────────────────────────────────────
# Aftersale tools
# ──────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
@patch("src.tools.fecmall.aftersale_tools.FecMallClient")
async def test_submit_complaint(mock_client_cls):
    """submit_complaint verifies order then returns complaint confirmation."""
    from src.tools.fecmall.aftersale_tools import submit_complaint
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "increment_id": "100000001",
            "status": "complete",
            "items": [{"name": "Item A"}],
        },
    })

    result = await submit_complaint.ainvoke({
        "order_id": "100000001",
        "reason": "质量缺陷",
        "description": "商品表面有划痕",
        "config": _make_config(),
    })

    assert "100000001" in result
    assert "投诉" in result or "complaint" in result.lower() or "提交" in result


@pytest.mark.asyncio
@patch("src.tools.fecmall.aftersale_tools.FecMallClient")
async def test_get_refund_status(mock_client_cls):
    """get_refund_status returns readable refund status."""
    from src.tools.fecmall.aftersale_tools import get_refund_status
    mock_http = _setup_mock_client(mock_client_cls)
    mock_http.get.return_value = _mock_response({
        "code": 200,
        "data": {
            "increment_id": "100000001",
            "status": "refunded",
            "refund_amount": "$25.00",
        },
    })

    result = await get_refund_status.ainvoke(
        {"order_id": "100000001", "config": _make_config()}
    )

    assert "100000001" in result
    assert "refund" in result.lower() or "退款" in result
