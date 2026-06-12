"""Production config — 12-Factor: tất cả từ environment variables.

Dự án: KnowledgeBaseAgent (RAG) — productionized cho Day 12.
"""
import os
import logging
from dataclasses import dataclass, field


@dataclass
class Settings:
    # Server
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # App
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "KnowledgeBase RAG Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    # LLM (mock by default — không cần API key, không tốn tiền)
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "mock-rag-llm"))

    # RAG
    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR", "data"))
    top_k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "3")))
    chunk_max_chars: int = field(default_factory=lambda: int(os.getenv("CHUNK_MAX_CHARS", "700")))
    # mock | local | openai  (mock = offline, deterministic)
    embedding_provider: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "mock")
    )

    # Security
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    allowed_origins: list = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )

    # Rate limiting
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    )

    # Budget (số request/ngày làm proxy cho cost — RAG mock không tốn tiền LLM)
    daily_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("DAILY_BUDGET_USD", "5.0"))
    )

    def validate(self):
        logger = logging.getLogger(__name__)
        if self.environment == "production":
            if self.agent_api_key == "dev-key-change-me":
                raise ValueError("AGENT_API_KEY must be set in production!")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set — dùng mock embeddings + mock LLM")
        return self


settings = Settings().validate()
