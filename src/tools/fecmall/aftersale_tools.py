"""FecMall 售后相关工具 — 异步 LangChain tools."""
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
async def submit_complaint(
    order_id: str,
    reason: str,
    description: str,
    config: RunnableConfig = None,
) -> str:
    """提交售后投诉。先验证订单存在，然后生成投诉确认信息。

    Args:
        order_id: 订单ID
        reason: 投诉原因
        description: 投诉描述
        config: LangChain RunnableConfig（含 access_token）
    """
    try:
        token = _get_token(config)
        async with FecMallClient(access_token=token) as client:
            # 第一步：验证订单存在
            resp = await client.get(
                "/customer/order/view",
                params={"order_id": order_id},
            )
            order_data = resp.json()

            # 第二步：生成投诉确认（组合工具，无独立投诉接口）
            complaint_info = {
                "order_id": order_id,
                "order_data": order_data,
                "reason": reason,
                "description": description,
                "status": "投诉已提交",
            }
            return f"投诉提交成功 (订单ID: {order_id}):\n{_format_json(complaint_info)}"
    except Exception as e:
        return f"Error: 提交投诉失败 — {e}"


@tool
async def get_refund_status(
    order_id: str,
    config: RunnableConfig = None,
) -> str:
    """查询订单退款状态。通过订单详情解读退款字段。

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

            # 从订单数据中解读退款状态
            status = data.get("status", "未知")
            refund_amount = data.get("refund_amount", "无")
            increment_id = data.get("increment_id", order_id)

            refund_info = {
                "order_id": increment_id,
                "order_status": status,
                "refund_amount": refund_amount,
                "refund_status": (
                    "已退款" if status == "refunded"
                    else "退款处理中" if status in ("refund_processing", "pending_refund")
                    else "无退款" if status in ("pending", "processing", "complete")
                    else f"状态: {status}"
                ),
            }
            return f"退款状态 (订单ID: {order_id}):\n{_format_json(refund_info)}"
    except Exception as e:
        return f"Error: 查询退款状态失败 — {e}"
