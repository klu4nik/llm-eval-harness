from __future__ import annotations

import hashlib
import math
import re

import chromadb
import pytest

from app.chunker import Chunk, load_corpus
from app.config import CORPUS_DIR
from app.golden import load_golden_set
from app.retriever import Retriever


class HashingEmbedder:
    """Deterministic bag-of-words embedder. Lets retrieval run in CI without a model."""

    def __init__(self, dims: int = 1024) -> None:
        self.dims = dims

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vec = [0.0] * self.dims
            for token in re.findall(r"[a-z_]{3,}", text.lower()):
                vec[int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dims] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


class FakeChatModel:
    name = "fake-llm"

    def __init__(self, answer: str = "Use locator.click(force=True). [1]") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        return self.answer


@pytest.fixture(scope="session")
def corpus_chunks() -> list[Chunk]:
    return load_corpus(CORPUS_DIR)


@pytest.fixture(scope="session")
def golden_set():
    return load_golden_set()


@pytest.fixture(scope="session")
def offline_retriever(corpus_chunks) -> Retriever:
    retriever = Retriever(chromadb.EphemeralClient(), "offline", HashingEmbedder())
    retriever.index(corpus_chunks)
    return retriever


@pytest.fixture
def fake_llm() -> FakeChatModel:
    return FakeChatModel()
