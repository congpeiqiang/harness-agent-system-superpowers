"""内置 Skill: 汇率转换"""
import httpx
from langchain_core.tools import tool
from ..base_skill import BaseSkill

@tool
async def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """将指定金额从一种货币转换为另一种货币。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://open.er-api.com/v6/latest/{from_currency.upper()}")
        data = resp.json()
        rate = data.get("rates", {}).get(to_currency.upper(), 0)
        if rate == 0:
            return f"无法获取 {from_currency} -> {to_currency} 的汇率"
        return f"{amount} {from_currency.upper()} = {amount * rate:.2f} {to_currency.upper()} (汇率: {rate})"

class CurrencyConvertSkill(BaseSkill):
    name = "currency_convert"
    description = "货币汇率转换工具"
    version = "1.0.0"
    def get_tools(self):
        return [convert_currency]
