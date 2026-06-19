"""FecMall 订单相关工具 — 异步 LangChain tools."""
import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.tools.fecmall.client import FecMallClient


def _get_token(config: RunnableConfig | None) -> str:
    return (config or {}).get("configurable", {}).get("access_token", "")


def _format_json(data: dict | list, indent: int = 2) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError):
        return str(data)


@tool
async def get_checkout_init(config: RunnableConfig = None) -> str:
    """获取结算初始化信息（地址、支付方式、配送方式等）。

    Args:
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get("/checkout/onepage/index")
            data = resp.json()
            return f"结算初始化信息:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 获取结算初始化信息失败 — {e}"


@tool
async def submit_order(
    address_id: str,
    payment_method: str,
    shipping_method: str,
    config: RunnableConfig = None,
) -> str:
    """提交订单。

    Args:
        address_id: 收货地址ID
        payment_method: 支付方式
        shipping_method: 配送方式
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/checkout/onepage/submitOrder",
                json={
                    "address_id": address_id,
                    "payment_method": payment_method,
                    "shipping_method": shipping_method,
                },
            )
            data = resp.json()
            return f"订单提交成功:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 提交订单失败 — {e}"


@tool
async def get_order_list(
    page: int = 1,
    config: RunnableConfig = None,
) -> str:
    """获取订单列表。

    Args:
        page: 页码，默认为1
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get(
                "/customer/order/list",
                params={"p": page},
            )
            data = resp.json()
            return f"订单列表 (第{page}页):\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 获取订单列表失败 — {e}"


@tool
async def get_order_detail(
    order_id: str,
    config: RunnableConfig = None,
) -> str:
    """获取订单详情。

    Args:
        order_id: 订单ID
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get(
                "/customer/order/view",
                params={"order_id": order_id},
            )
            data = resp.json()
            return f"订单详情 (订单ID: {order_id}):\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 获取订单详情失败 — {e}"
