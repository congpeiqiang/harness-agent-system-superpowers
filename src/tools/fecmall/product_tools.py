"""FecMall 商品相关工具 — 异步 LangChain tools."""
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.tools.fecmall.client import FecMallClient
from src.tools.fecmall.utils import get_token, format_json


@tool
async def search_products(keyword: str, page: int = 1, config: RunnableConfig = None) -> str:
    """搜索 FecMall 商品。

    Args:
        keyword: 搜索关键词
        page: 页码，默认为1
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get(
                "/catalogsearch/index/index",
                params={"q": keyword, "p": page},
            )
            data = resp.json()
            return f"搜索结果 (关键词: {keyword}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 搜索商品失败 — {e}"


@tool
async def get_product_detail(product_id: str, config: RunnableConfig = None) -> str:
    """获取 FecMall 商品详情。

    Args:
        product_id: 商品ID
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get(
                "/catalog/product/index",
                params={"product_id": product_id},
            )
            data = resp.json()
            return f"商品详情 (ID: {product_id}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 获取商品详情失败 — {e}"


@tool
async def get_category_products(category_id: str, page: int = 1, config: RunnableConfig = None) -> str:
    """获取 FecMall 分类下的商品列表。

    Args:
        category_id: 分类ID
        page: 页码，默认为1
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get(
                "/catalog/category/product",
                params={"category_id": category_id, "p": page},
            )
            data = resp.json()
            return f"分类商品 (分类ID: {category_id}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 获取分类商品失败 — {e}"


@tool
async def get_product_reviews(product_id: str, config: RunnableConfig = None) -> str:
    """获取 FecMall 商品评论列表。

    Args:
        product_id: 商品ID
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get(
                "/catalog/product/reviewlist",
                params={"product_id": product_id},
            )
            data = resp.json()
            return f"商品评论 (商品ID: {product_id}):\n{format_json(data)}"
    except Exception as e:
        return f"Error: 获取商品评论失败 — {e}"


@tool
async def get_home_info(config: RunnableConfig = None) -> str:
    """获取 FecMall 首页信息（Banner、热销商品等）。

    Args:
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get("/home/index")
            data = resp.json()
            return f"首页信息:\n{format_json(data)}"
    except Exception as e:
        return f"Error: 获取首页信息失败 — {e}"
