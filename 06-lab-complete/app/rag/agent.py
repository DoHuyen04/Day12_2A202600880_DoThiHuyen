from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Retrieve the most relevant chunks for the question.
        results = self.store.search(question, top_k=top_k)

        # 2. Build a context block from the retrieved chunks.
        if results:
            context = "\n\n".join(
                f"[{i + 1}] {r['content']}" for i, r in enumerate(results)
            )
        else:
            context = "(no relevant context found)"

        # 3. Assemble the RAG prompt and call the LLM.
        prompt = (
            "Answer the question using only the context below.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
