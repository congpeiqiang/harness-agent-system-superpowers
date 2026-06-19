"""FecMall Appserver API 异步客户端"""
import httpx
from src.config.settings import get_settings

class FecMallClient:
    """FecMall Appserver API 异步客户端。使用 httpx.AsyncClient，支持 async with。"""
    def __init__(self, access_token: str | None = None):
        settings = get_settings()
        self.base_url = settings.fecmall.base_url
        self.currency = settings.fecmall.default_currency
        self.lang = settings.fecmall.default_lang
        self.timeout = settings.fecmall.timeout
        self.access_token = access_token
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> httpx.AsyncClient:
        headers = {
            "fecshop-currency": self.currency,
            "fecshop-lang": self.lang,
        }
        if self.access_token:
            headers["access-token"] = self.access_token
        self._client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=self.timeout,
        )
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
        return False
