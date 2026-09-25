"""Vector index over the corpus chunks (ChromaDB, cosine distance)."""

from __future__ import annotations

from dataclasses import dataclass

import chromadb

from app.chunker import Chunk
from app.llm import Embedder


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc: str
    section: str
    text: str
    score: float  # cosine similarity, higher is better


class Retriever:
    def __init__(self, client: chromadb.ClientAPI, collection: str, embedder: Embedder) -> None:
        self._embedder = embedder
        self._collection = client.get_or_create_collection(
            name=collection, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )

    def index(self, chunks: list[Chunk], batch_size: int = 32) -> None:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            self._collection.upsert(
                ids=[c.chunk_id for c in batch],
                embeddings=self._embedder.embed([c.text for c in batch]),
                documents=[c.text for c in batch],
                metadatas=[{"doc": c.doc, "section": c.section} for c in batch],
            )

    def count(self) -> int:
        return self._collection.count()

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        result = self._collection.query(
            query_embeddings=self._embedder.embed([query]), n_results=top_k
        )
        return [
            RetrievedChunk(
                chunk_id=chunk_id,
                doc=meta["doc"],
                section=meta["section"],
                text=text,
                score=1.0 - distance,
            )
            for chunk_id, meta, text, distance in zip(
                result["ids"][0], result["metadatas"][0], result["documents"][0], result["distances"][0]
            )
        ]
