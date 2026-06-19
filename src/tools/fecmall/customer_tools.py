"""FecMall 客户相关工具 — 异步 LangChain tools."""
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
async def login(
    email: str,
    password: str,
) -> str:
    """用户登录，获取 access_token。无需已有 token。

    Args:
        email: 用户邮箱
        password: 用户密码
    """
    try:
        async with FecMallClient() as client:
            resp = await client.post(
                "/customer/login",
                json={"email": email, "password": password},
            )
            data = resp.json()
            return f"登录成功:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 登录失败 — {e}"


@tool
async def register(
    email: str,
    password: str,
    firstname: str = "",
    lastname: str = "",
) -> str:
    """用户注册，无需已有 token。

    Args:
        email: 用户邮箱
        password: 用户密码
        firstname: 名，可选
        lastname: 姓，可选
    """
    try:
        async with FecMallClient() as client:
            resp = await client.post(
                "/customer/register",
                json={
                    "email": email,
                    "password": password,
                    "firstname": firstname,
                    "lastname": lastname,
                },
            )
            data = resp.json()
            return f"注册成功:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 注册失败 — {e}"


@tool
async def get_user_profile(config: RunnableConfig = None) -> str:
    """获取当前用户个人资料。

    Args:
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get("/customer/account/index")
            data = resp.json()
            return f"用户资料:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 获取用户资料失败 — {e}"


@tool
async def update_profile(
    firstname: str = "",
    lastname: str = "",
    config: RunnableConfig = None,
) -> str:
    """更新用户个人资料。

    Args:
        firstname: 名
        lastname: 姓
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/customer/account/editSubmit",
                json={"firstname": firstname, "lastname": lastname},
            )
            data = resp.json()
            return f"更新用户资料成功:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 更新用户资料失败 — {e}"


@tool
async def get_address_list(config: RunnableConfig = None) -> str:
    """获取收货地址列表。

    Args:
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.get("/customer/address/list")
            data = resp.json()
            return f"收货地址列表:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 获取收货地址列表失败 — {e}"


@tool
async def add_address(
    firstname: str,
    lastname: str,
    street: str,
    city: str,
    country: str,
    telephone: str,
    config: RunnableConfig = None,
) -> str:
    """添加收货地址。

    Args:
        firstname: 名
        lastname: 姓
        street: 街道地址
        city: 城市
        country: 国家代码
        telephone: 电话号码
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/customer/address/editSubmit",
                json={
                    "firstname": firstname,
                    "lastname": lastname,
                    "street": street,
                    "city": city,
                    "country": country,
                    "telephone": telephone,
                },
            )
            data = resp.json()
            return f"添加收货地址成功:\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 添加收货地址失败 — {e}"


@tool
async def remove_address(
    address_id: str,
    config: RunnableConfig = None,
) -> str:
    """删除收货地址。

    Args:
        address_id: 地址ID
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            resp = await client.post(
                "/customer/address/remove",
                json={"address_id": address_id},
            )
            data = resp.json()
            return f"删除收货地址成功 (地址ID: {address_id}):\n{_format_json(data)}"
    except Exception as e:
        return f"Error: 删除收货地址失败 — {e}"
