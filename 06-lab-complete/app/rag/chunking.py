from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if not 0 <= overlap < chunk_size:
            raise ValueError(
                f"overlap must satisfy 0 <= overlap < chunk_size, "
                f"got overlap={overlap}, chunk_size={chunk_size}"
            )
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3, chunk_size: int | None = None) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)
        # Optional character budget so chunks are size-comparable to the other
        # strategies (used by ChunkingStrategyComparator for a fair comparison).
        # When None, behavior is purely sentence-count based.
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split on sentence-ending punctuation followed by whitespace,
        # keeping the punctuation attached to the sentence.
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return []

        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for sentence in sentences:
            hit_sentence_cap = len(current) >= self.max_sentences_per_chunk
            hit_size_cap = (
                self.chunk_size is not None
                and current
                and current_len + 1 + len(sentence) > self.chunk_size
            )
            if current and (hit_sentence_cap or hit_size_cap):
                chunks.append(" ".join(current))
                current, current_len = [], 0
            current.append(sentence)
            current_len += len(sentence) + (1 if len(current) > 1 else 0)

        if current:
            chunks.append(" ".join(current))
        return chunks


class ParagraphChunker:
    """
    Context-aware chunking: keep each paragraph/section intact.

    Rules:
        - Split text into blocks on blank lines.
        - A markdown header line (starting with '#') is attached to the block
          that follows it, so a heading never becomes a lonely chunk and each
          chunk carries its section title as context.
        - Each block becomes one chunk, so a list or idea that lives in a single
          paragraph is never cut in half.
        - If a single block is longer than max_chars, fall back to packing whole
          sentences into <= max_chars windows (so an oversized paragraph is split
          at sentence boundaries, never mid-sentence).
    """

    _SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_chars: int = 700) -> None:
        if max_chars <= 0:
            raise ValueError(f"max_chars must be positive, got {max_chars}")
        self.max_chars = max_chars

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        chunks: list[str] = []
        header_prefix = ""

        for block in blocks:
            lines = block.splitlines()
            # A header-only block is held and prepended to the next real block.
            if all(line.lstrip().startswith("#") for line in lines):
                header_prefix += block + "\n"
                continue

            unit = f"{header_prefix}{block}".strip()
            header_prefix = ""

            if len(unit) <= self.max_chars:
                chunks.append(unit)
            else:
                chunks.extend(self._pack_sentences(unit))

        # A trailing header with no following body still becomes its own chunk.
        if header_prefix.strip():
            chunks.append(header_prefix.strip())
        return chunks

    def _pack_sentences(self, text: str) -> list[str]:
        sentences = [s.strip() for s in self._SENTENCE_SPLIT_RE.split(text) if s.strip()]
        windows: list[str] = []
        current: list[str] = []
        current_len = 0
        for sentence in sentences:
            extra = len(sentence) + (1 if current else 0)
            if current and current_len + extra > self.max_chars:
                windows.append(" ".join(current))
                current, current_len = [], 0
            current.append(sentence)
            current_len += len(sentence) + (1 if len(current) > 1 else 0)
        if current:
            windows.append(" ".join(current))
        return windows


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: text already fits within the size budget.
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        # No separators left: fall back to hard fixed-size slicing.
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        separator, *rest = remaining_separators

        # An empty separator means "split into characters" — hard slice.
        if separator == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        pieces = current_text.split(separator)
        if len(pieces) == 1:
            # This separator did not occur; try the next one.
            return self._split(current_text, rest)

        sub_chunks: list[str] = []
        for piece in pieces:
            if not piece:
                continue
            if len(piece) <= self.chunk_size:
                sub_chunks.append(piece)
            else:
                # Piece still too big: recurse with the remaining separators.
                sub_chunks.extend(self._split(piece, rest))

        # Merge adjacent small pieces back together — rejoined with the SAME
        # separator so the original text is preserved — up to chunk_size. This
        # avoids over-fragmentation (one tiny chunk per line) while never
        # exceeding the size budget.
        return self._merge(sub_chunks, separator)

    def _merge(self, parts: list[str], separator: str) -> list[str]:
        merged: list[str] = []
        current = ""
        for part in parts:
            candidate = part if not current else current + separator + part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    merged.append(current)
                current = part
        if current:
            merged.append(current)
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size).chunk(text),
            # Pass chunk_size so sentence chunks are size-comparable to the
            # other two strategies (fair comparison, not just sentence count).
            "by_sentences": SentenceChunker(chunk_size=chunk_size).chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }

        result: dict = {}
        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count else 0.0
            result[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return result
