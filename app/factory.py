"""Wiring for the real (Ollama + persistent Chroma) setup."""

from __future__ import annotations

import re

import chromadb

from app.bot import RagBot
from app.chunker import load_corpus
from app.config import CORPUS_DIR, INDEX_DIR, Settings
from app.llm import OllamaChatModel, OllamaEmbedder
from app.retriever import Retriever


def build_retriever(settings: Settings) -> Retriever:
    client = chromadb.PersistentClient(path=str(INDEX_DIR))
    # Index name includes embed model and chunk size: changing either must not reuse a stale index.
    raw = f"{settings.collection}-{settings.embed_model}-{settings.chunk_max_chars}"
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", raw)  # Chroma allows only these characters
    return Retriever(client, name, OllamaEmbedder(settings))


def build_index(settings: Settings) -> int:
    retriever = build_retriever(settings)
    retriever.index(load_corpus(CORPUS_DIR, settings.chunk_max_chars))
    return retriever.count()


def build_bot(settings: Settings | None = None) -> RagBot:
    settings = settings or Settings()
    retriever = build_retriever(settings)
    if retriever.count() == 0:
        raise RuntimeError("Index is empty. Run: python -m app.cli index")
    return RagBot(retriever, OllamaChatModel(settings), settings.top_k)
