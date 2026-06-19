"""Tests for RAG knowledge base modules."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.rag.loader import DocumentLoader


class TestDocumentLoader:
    """Test DocumentLoader.load_all() reads .md files from knowledge_base/."""

    def test_load_all_returns_documents(self):
        loader = DocumentLoader()
        docs = loader.load_all()
        assert isinstance(docs, list)
        assert len(docs) >= 8, f"Expected at least 8 documents, got {len(docs)}"

    def test_load_all_each_doc_has_content(self):
        loader = DocumentLoader()
        docs = loader.load_all()
        for doc in docs:
            assert hasattr(doc, "page_content")
            assert len(doc.page_content.strip()) > 0

    def test_load_all_each_doc_has_metadata(self):
        loader = DocumentLoader()
        docs = loader.load_all()
        for doc in docs:
            assert hasattr(doc, "metadata")
            assert "source" in doc.metadata
            assert "category" in doc.metadata

    def test_load_all_covers_both_categories(self):
        loader = DocumentLoader()
        docs = loader.load_all()
        categories = {doc.metadata["category"] for doc in docs}
        assert "faq" in categories
        assert "policies" in categories

    def test_load_all_faq_docs_contain_expected_content(self):
        loader = DocumentLoader()
        docs = loader.load_all()
        faq_docs = [d for d in docs if d.metadata["category"] == "faq"]
        all_text = " ".join(d.page_content for d in faq_docs)
        assert "商品" in all_text or "货" in all_text
        assert "订单" in all_text or "物流" in all_text

    def test_load_all_policies_docs_contain_expected_content(self):
        loader = DocumentLoader()
        docs = loader.load_all()
        policy_docs = [d for d in docs if d.metadata["category"] == "policies"]
        all_text = " ".join(d.page_content for d in policy_docs)
        assert "退换" in all_text

    def test_load_all_custom_base_dir(self, tmp_path):
        # Create a temp knowledge base structure
        faq_dir = tmp_path / "faq"
        faq_dir.mkdir()
        (faq_dir / "test.md").write_text("# Test FAQ\n\nTest content", encoding="utf-8")
        loader = DocumentLoader(base_dir=str(tmp_path))
        docs = loader.load_all()
        assert len(docs) == 1
        assert "Test content" in docs[0].page_content
        assert docs[0].metadata["category"] == "faq"

    def test_load_all_empty_dir(self, tmp_path):
        loader = DocumentLoader(base_dir=str(tmp_path))
        docs = loader.load_all()
        assert docs == []
