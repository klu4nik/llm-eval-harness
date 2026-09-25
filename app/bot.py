"""The system under test: a RAG bot that answers Playwright (Python) questions.

`ask()` returns the answer together with the retrieved context, latency and
model name. The eval layer needs all of it: faithfulness is judged against the
context, retrieval metrics against the chunk metadata.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.config import REFUSAL_TEXT
from app.llm import ChatModel
from app.retriever import RetrievedChunk, Retriever

SYSTEM_PROMPT = f"""You answer questions about Playwright for Python.
Use ONLY the documentation context provided by the user message.
Rules:
- If the context does not contain the answer, reply exactly: {REFUSAL_TEXT}
- Use the Python API (snake_case), never JavaScript, Java or C#.
- Keep answers short. Include a code snippet only if the context has one.
- Cite the context blocks you used as [1], [2], ..."""


@dataclass
class BotResponse:
    question: str
    answer: str
    contexts: list[RetrievedChunk]
    model: str
    latency_ms: float
    refused: bool = field(init=False)

    def __post_init__(self) -> None:
        self.refused = REFUSAL_TEXT.lower() in self.answer.lower()

    @property
    def context_texts(self) -> list[str]:
        return [c.text for c in self.contexts]


def build_user_prompt(question: str, contexts: list[RetrievedChunk]) -> str:
    blocks = "\n\n".join(
        f"[{n}] ({c.doc} / {c.section})\n{c.text}" for n, c in enumerate(contexts, start=1)
    )
    return f"Documentation context:\n\n{blocks}\n\nQuestion: {question}"


class RagBot:
    def __init__(self, retriever: Retriever, llm: ChatModel, top_k: int = 4) -> None:
        self._retriever = retriever
        self._llm = llm
        self._top_k = top_k

    def ask(self, question: str) -> BotResponse:
        started = time.perf_counter()
        contexts = self._retriever.search(question, self._top_k)
        answer = self._llm.complete(SYSTEM_PROMPT, build_user_prompt(question, contexts))
        latency_ms = (time.perf_counter() - started) * 1000
        return BotResponse(question, answer, contexts, self._llm.name, latency_ms)
