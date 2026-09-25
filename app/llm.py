"""Thin interfaces over the model backends.

The bot depends on these Protocols, not on Ollama directly, so unit tests can
plug in fakes and run in CI without a model.
"""

from __future__ import annotations

from typing import Protocol

import ollama

from app.config import Settings


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class ChatModel(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str: ...


class OllamaEmbedder:
    def __init__(self, settings: Settings) -> None:
        self._client = ollama.Client(host=settings.ollama_host)
        self._model = settings.embed_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(v) for v in self._client.embed(model=self._model, input=texts).embeddings]


class OllamaChatModel:
    def __init__(self, settings: Settings) -> None:
        self._client = ollama.Client(host=settings.ollama_host)
        self.name = settings.llm_model
        self._options = {"temperature": settings.temperature, "seed": settings.seed}

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat(
            model=self.name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            options=self._options,
        )
        return response.message.content.strip()
