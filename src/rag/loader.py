"""文档加载器 — 从 knowledge_base/ 目录加载 Markdown 文档"""
import os
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document


class DocumentLoader:
    """加载 knowledge_base 目录下的所有 .md 文件"""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # 默认相对于项目根目录
            project_root = Path(__file__).resolve().parent.parent.parent
            self.base_dir = project_root / "knowledge_base"
        else:
            self.base_dir = Path(base_dir)

    def load_all(self) -> list[Document]:
        """加载所有子目录下的 .md 文件，返回 Document 列表"""
        documents: list[Document] = []

        if not self.base_dir.exists():
            return documents

        for category_dir in sorted(self.base_dir.iterdir()):
            if not category_dir.is_dir():
                continue
            category = category_dir.name
            for md_file in sorted(category_dir.glob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                if content.strip():
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(md_file.relative_to(self.base_dir)),
                            "category": category,
                            "filename": md_file.name,
                        },
                    )
                    documents.append(doc)

        return documents
