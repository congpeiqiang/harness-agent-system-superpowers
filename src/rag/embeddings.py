"""向量化服务 — 使用 OpenAI Embeddings 生成文本向量"""
from langchain_openai import OpenAIEmbeddings
from src.config.settings import get_settings


class EmbeddingService:
    """封装 OpenAI Embeddings，提供文本向量化接口"""

    def __init__(self):
        settings = get_settings()
        api_key = settings.embedding.api_key or settings.openai_api_key
        self._embeddings = OpenAIEmbeddings(
            base_url=settings.embedding.base_url,
            api_key=api_key or "not-set",
            model=settings.embedding.model,
        )

    async def embed_text(self, text: str) -> list[float]:
        """将单条文本向量化"""
        return await self._embeddings.aembed_query(text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """将多条文本批量向量化"""
        return await self._embeddings.aembed_documents(texts)
