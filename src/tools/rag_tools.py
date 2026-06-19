"""RAG 知识库检索工具"""
from typing import Optional
from langchain_core.tools import tool
from src.rag.retriever import RAGRetriever


@tool
async def rag_search(query: str, category: Optional[str] = None) -> str:
    """从知识库中搜索与用户问题相关的信息。

    Args:
        query: 用户的搜索问题或关键词
        category: 可选，搜索范围限制。'faq' 只搜索常见问题，'policies' 只搜索政策文档。不传则搜索全部。

    Returns:
        搜索结果，包含相关文档片段和来源信息
    """
    try:
        retriever = RAGRetriever.get_instance()
        results = await retriever.search(query=query, top_k=5, category=category)

        if not results:
            return "未找到相关知识库内容，建议联系人工客服获取帮助。"

        formatted = []
        for i, r in enumerate(results, 1):
            source = r.get("source", "未知")
            score = r.get("score", 0)
            text = r.get("text", "")
            formatted.append(
                f"[{i}] (相关度: {score:.2f}, 来源: {source})\n{text}"
            )

        return "\n\n".join(formatted)
    except Exception as e:
        return f"Error: RAG 搜索失败 - {str(e)}"
