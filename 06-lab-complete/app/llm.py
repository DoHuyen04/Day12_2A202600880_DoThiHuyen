"""
LLM backend cho RAG agent.

Mặc định dùng mock LLM (offline, không cần API key, không tốn tiền) — phù hợp
demo/deploy. Khi set OPENAI_API_KEY, tự chuyển sang gọi OpenAI thật.

Hàm `make_llm()` trả về callable `llm_fn(prompt: str) -> str` đúng interface mà
`KnowledgeBaseAgent` yêu cầu.
"""
from __future__ import annotations

import re
from typing import Callable

from app.config import settings


def _mock_llm(prompt: str) -> str:
    """
    Mock LLM extractive: tóm tắt context trong prompt thành câu trả lời ngắn.

    Prompt do agent dựng có dạng:
        Answer the question using only the context below.
        Context:
        [1] ...
        [2] ...
        Question: <q>
        Answer:
    Ta trích phần Context để tạo câu trả lời gọn (không bịa ngoài context).
    """
    context = ""
    m = re.search(r"Context:\s*(.*?)\s*Question:", prompt, re.DOTALL)
    if m:
        context = m.group(1).strip()

    if not context or context == "(no relevant context found)":
        return ("Tôi không tìm thấy thông tin liên quan trong cơ sở tri thức "
                "để trả lời câu hỏi này.")

    # Lấy ~2 câu đầu của chunk top-1 làm câu trả lời súc tích.
    first_chunk = re.sub(r"^\[\d+\]\s*", "", context.splitlines()[0]).strip()
    sentences = re.split(r"(?<=[.!?])\s+", first_chunk)
    answer = " ".join(sentences[:2]).strip()
    return f"(mock-rag) {answer}" if answer else f"(mock-rag) {first_chunk[:300]}"


def _openai_llm(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=settings.llm_model if settings.llm_model.startswith("gpt") else "gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=400,
    )
    return resp.choices[0].message.content or ""


def make_llm() -> Callable[[str], str]:
    """Chọn backend dựa trên config. Fallback an toàn về mock nếu OpenAI lỗi."""
    if settings.openai_api_key:
        def _safe_openai(prompt: str) -> str:
            try:
                return _openai_llm(prompt)
            except Exception:
                return _mock_llm(prompt)
        return _safe_openai
    return _mock_llm
