"""
Knowledge base bootstrap — load documents từ DATA_DIR, build EmbeddingStore và
KnowledgeBaseAgent. Gọi 1 lần lúc startup (lifespan).
"""
from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.llm import make_llm
from app.rag.agent import KnowledgeBaseAgent
from app.rag.chunking import ParagraphChunker
from app.rag.embeddings import FallbackEmbedder, MockEmbedder
from app.rag.models import Document
from app.rag.store import EmbeddingStore

logger = logging.getLogger(__name__)

_ALLOWED_EXT = {".md", ".txt"}
_VI_CHARS = set("ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ")


def _detect_language(text: str) -> str:
    return "vi" if any(ch in _VI_CHARS for ch in text.lower()) else "en"


def _build_embedder():
    """Chọn embedder theo config; bọc FallbackEmbedder để không crash runtime."""
    provider = settings.embedding_provider.lower()
    if provider == "openai" and settings.openai_api_key:
        from app.rag.embeddings import OpenAIEmbedder
        return FallbackEmbedder(OpenAIEmbedder())
    if provider == "local":
        from app.rag.embeddings import LocalEmbedder
        return FallbackEmbedder(LocalEmbedder())
    return MockEmbedder()  # deterministic, offline


def load_documents(data_dir: str) -> list[Document]:
    docs: list[Document] = []
    base = Path(data_dir)
    if not base.exists():
        logger.warning("DATA_DIR '%s' không tồn tại", data_dir)
        return docs
    for path in sorted(base.iterdir()):
        if path.suffix.lower() not in _ALLOWED_EXT or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                id=path.stem,
                content=content,
                metadata={
                    "source": path.name,
                    "lang": _detect_language(content),
                },
            )
        )
    return docs


def build_agent() -> tuple[KnowledgeBaseAgent, EmbeddingStore, dict]:
    """Load KB và trả về (agent, store, stats)."""
    embedder = _build_embedder()
    store = EmbeddingStore(
        embedding_fn=embedder,
        chunker=ParagraphChunker(max_chars=settings.chunk_max_chars),
    )
    docs = load_documents(settings.data_dir)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store=store, llm_fn=make_llm())
    stats = {
        "documents": len(docs),
        "chunks": store.get_collection_size(),
        "embedder": getattr(embedder, "_backend_name", "mock"),
    }
    logger.info("Knowledge base loaded: %s", stats)
    return agent, store, stats
