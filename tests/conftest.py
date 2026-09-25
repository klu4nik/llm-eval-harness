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


def pytest_addoption(parser):
    parser.addoption(
        "--eval-cases",
        default="smoke",
        help="golden cases for the DeepEval suite: smoke (default), all, or ids like GS-001,GS-004",
    )


def ollama_or_skip(host: str, model: str | None = None):
    """Return an Ollama client, or skip the test if the server (or the model) is not there."""
    ollama = pytest.importorskip("ollama")
    try:
        client = ollama.Client(host=host)
        available = {m.model for m in client.list().models}
    except Exception:
        pytest.skip(f"Ollama is not reachable at {host}")
    if model and model not in available and f"{model}:latest" not in available:
        pytest.skip(f"model {model} is not pulled (ollama pull {model})")
    return client


@pytest.fixture(scope="session")
def real_bot():
    """The real bot (Ollama + persistent index). Only for tests marked `llm`."""
    from app.config import Settings

    settings = Settings()
    ollama_or_skip(settings.ollama_host, settings.llm_model)
    from app.factory import build_bot

    return build_bot(settings)


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
