"""FecMall 工具共享实用函数。"""
import json
from langchain_core.runnables import RunnableConfig


def get_token(config: RunnableConfig | None) -> str:
    """从 RunnableConfig 中提取 access_token。"""
    return (config or {}).get("configurable", {}).get("access_token", "")


def format_json(data: dict | list, indent: int = 2) -> str:
    """Pretty-print JSON data for readable tool output."""
    try:
        return json.dumps(data, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError):
        return str(data)
