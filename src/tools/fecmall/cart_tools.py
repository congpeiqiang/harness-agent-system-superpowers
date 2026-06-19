"""FecMall 购物车相关工具 — 异步 LangChain tools."""
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.tools.fecmall.client import FecMallClient
from src.tools.fecmall.utils import get_token, format_json


@tool
async def get_cart(config: RunnableConfig = None) -> str:
    """获取购物车内容。

    Args:
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get("/checkout/cart/index")
            data = resp.json()
            return f"购物车内容:\n{format_json(data)}"
    except Exception as e:
        return f"Error: 获取购物车失败 — {e}"


@tool
async def add_to_cart(
    product_id: str,
    qty: int = 1,
    config: RunnableConfig = None,
) -> str:
    """将商品添加到购物车。

    Args:
        product_id: 商品ID
        qty: 数量，默认为1
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/catalog/product/addtocart",
                json={"product_id": product_id, "qty": qty},
            )
            data = resp.json()
            return f"添加商品到购物车成功 (商品ID: {product_id}, 数量: {qty}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 添加商品到购物车失败 — {e}"


@tool
async def update_cart_item(
    item_id: str,
    qty: int,
    config: RunnableConfig = None,
) -> str:
    """更新购物车中商品的数量。

    Args:
        item_id: 购物车条目ID
        qty: 新数量
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/checkout/cart/updateinfo",
                json={"item_id": item_id, "qty": qty},
            )
            data = resp.json()
            return f"更新购物车条目成功 (条目ID: {item_id}, 数量: {qty}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 更新购物车条目失败 — {e}"


@tool
async def remove_cart_item(
    item_id: str,
    config: RunnableConfig = None,
) -> str:
    """从购物车中移除商品（将数量设为0）。

    Args:
        item_id: 购物车条目ID
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/checkout/cart/updateinfo",
                json={"item_id": item_id, "qty": 0},
            )
            data = resp.json()
            return f"删除购物车条目成功 (条目ID: {item_id}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 删除购物车条目失败 — {e}"
