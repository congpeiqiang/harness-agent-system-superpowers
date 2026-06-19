"""Milvus 向量数据库客户端管理"""
from typing import Optional
from pymilvus import (
    MilvusClient,
    FieldSchema,
    CollectionSchema,
    DataType,
)
from src.config.settings import get_settings


class MilvusManager:
    """封装 Milvus 连接、集合管理、文档插入与搜索"""

    def __init__(self):
        settings = get_settings()
        self._uri = settings.milvus.uri
        self._token = settings.milvus.token
        self._collection_name = settings.milvus.collection_name
        self._client: Optional[MilvusClient] = None

    def connect(self) -> None:
        """连接到 Milvus 实例"""
        connect_params = {"uri": self._uri}
        if self._token:
            connect_params["token"] = self._token
        self._client = MilvusClient(**connect_params)
        self._create_collection()

    def _create_collection(self) -> None:
        """如果集合不存在则创建，包含 id、text、category、embedding 字段"""
        if self._client.has_collection(self._collection_name):
            return

        schema = self._client.create_schema(auto_id=True, enable_dynamic_field=True)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("text", DataType.VARCHAR, max_length=65535)
        schema.add_field("category", DataType.VARCHAR, max_length=256)
        schema.add_field("source", DataType.VARCHAR, max_length=512)
        schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=1536)

        index_params = self._client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        self._client.create_collection(
            collection_name=self._collection_name,
            schema=schema,
            index_params=index_params,
        )

    def insert_documents(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        categories: list[str],
        sources: list[str],
    ) -> int:
        """插入文档及其向量到集合，返回插入数量"""
        data = []
        for text, embedding, category, source in zip(
            texts, embeddings, categories, sources
        ):
            data.append({
                "text": text,
                "embedding": embedding,
                "category": category,
                "source": source,
            })

        if not data:
            return 0

        result = self._client.insert(
            collection_name=self._collection_name,
            data=data,
        )
        return result.get("insert_count", len(data))

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> list[dict]:
        """使用向量相似度搜索文档"""
        search_params = {"metric_type": "COSINE", "params": {}}

        filter_expr = None
        if category:
            filter_expr = f'category == "{category}"'

        results = self._client.search(
            collection_name=self._collection_name,
            data=[query_embedding],
            limit=top_k,
            output_fields=["text", "category", "source"],
            search_params=search_params,
            filter=filter_expr,
        )

        documents = []
        if results and results[0]:
            for hit in results[0]:
                documents.append({
                    "text": hit["entity"]["text"],
                    "category": hit["entity"]["category"],
                    "source": hit["entity"]["source"],
                    "score": hit["distance"],
                })

        return documents

    def close(self) -> None:
        """关闭 Milvus 连接"""
        if self._client:
            self._client.close()
            self._client = None
