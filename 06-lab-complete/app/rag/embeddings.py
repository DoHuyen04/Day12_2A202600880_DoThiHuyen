from __future__ import annotations

import hashlib
import math

LOCAL_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI()

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


_mock_embed = MockEmbedder()


class FallbackEmbedder:
    """Wrap a primary embedder and fall back to mock if it fails at call time.

    The constructor try/except in main.py only protects against setup errors.
    Real embedders (OpenAI, local models) can also fail *while embedding* — a
    dropped network, a rate limit, an out-of-memory model. This wrapper catches
    that first runtime failure, warns once, and switches permanently to the
    fallback so a long indexing run does not crash midway.
    """

    def __init__(self, primary, fallback=_mock_embed) -> None:
        self._primary = primary
        self._fallback = fallback
        self._failed = False
        self._backend_name = getattr(primary, "_backend_name", primary.__class__.__name__)

    def __call__(self, text: str) -> list[float]:
        if self._failed:
            return self._fallback(text)
        try:
            return self._primary(text)
        except Exception as exc:  # noqa: BLE001 - intentionally broad: any failure -> fallback
            self._failed = True
            fallback_name = getattr(self._fallback, "_backend_name", "mock embeddings fallback")
            print(
                f"[warn] embedder '{self._backend_name}' failed at runtime "
                f"({type(exc).__name__}: {exc}); falling back to {fallback_name}."
            )
            self._backend_name = f"{fallback_name} (fallback after runtime error)"
            return self._fallback(text)
