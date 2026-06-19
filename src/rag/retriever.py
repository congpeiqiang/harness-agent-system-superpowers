"""RAG 检索器 — 整合文档加载、向量化、Milvus 存储与搜索"""
import structlog
from typing import Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.loader import DocumentLoader
from src.rag.embeddings import EmbeddingService
from src.rag.milvus_client import MilvusManager

logger = structlog.get_logger(__name__)


class RAGRetriever:
    """RAG 检索器单例，管理知识库的索引与检索"""

    _instance: Optional["RAGRetriever"] = None

    def __new__(cls) -> "RAGRetriever":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._loader = DocumentLoader()
        self._embedding_service = EmbeddingService()
        self._milvus = MilvusManager()
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n## ", "\n### ", "\n\n", "\n", "。", " ", ""],
        )
        self._initialized = True

    async def initialize(self) -> None:
        """初始化：连接 Milvus，加载文档，分块并向量化后写入"""
        logger.info("rag_initializing", step="connect_milvus")
        self._milvus.connect()

        logger.info("rag_initializing", step="load_documents")
        docs = self._loader.load_all()
        if not docs:
            logger.warning("rag_no_documents_found")
            return

        # 分块
        chunks: list[str] = []
        chunk_categories: list[str] = []
        chunk_sources: list[str] = []
        for doc in docs:
            splits = self._text_splitter.split_text(doc.page_content)
            for split in splits:
                chunks.append(split)
                chunk_categories.append(doc.metadata["category"])
                chunk_sources.append(doc.metadata["source"])

        logger.info("rag_chunks_created", count=len(chunks))

        # 批量向量化
        embeddings = await self._embedding_service.embed_documents(chunks)
        logger.info("rag_embeddings_created", count=len(embeddings))

        # 写入 Milvus
        count = self._milvus.insert_documents(
            texts=chunks,
            embeddings=embeddings,
            categories=chunk_categories,
            sources=chunk_sources,
        )
        logger.info("rag_documents_inserted", count=count)

    async def search(
        self, query: str, top_k: int = 5, category: Optional[str] = None
    ) -> list[dict]:
        """根据查询文本进行语义搜索"""
        query_embedding = await self._embedding_service.embed_text(query)
        results = self._milvus.search(
            query_embedding=query_embedding,
            top_k=top_k,
            category=category,
        )
        return results

    def close(self) -> None:
        """关闭 Milvus 连接并重置单例"""
        self._milvus.close()
        RAGRetriever._instance = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "RAGRetriever":
        """获取单例实例"""
        return cls()
