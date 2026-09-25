"""Runtime settings. Everything can be overridden with environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
GOLDEN_SET = ROOT / "data" / "golden_set.json"
INDEX_DIR = ROOT / ".index"

# Upstream docs are pinned to one commit so the corpus (and the golden set built on it) is reproducible.
PLAYWRIGHT_DOCS_COMMIT = "afa6836a5119b38809dd7670a03c1e7b2c2632e9"
PLAYWRIGHT_DOCS = [
    "actionability",
    "locators",
    "auth",
    "browser-contexts",
    "network",
    "dialogs",
    "downloads",
    "navigations",
    "test-assertions-csharp-java-python",
    "test-runners-python",
    "trace-viewer",
    "api-testing-python",
]

REFUSAL_TEXT = "I don't know based on the provided documentation."


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.1:8b")
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
    chunk_max_chars: int = int(os.getenv("CHUNK_MAX_CHARS", "1500"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    seed: int = int(os.getenv("LLM_SEED", "42"))
    collection: str = os.getenv("INDEX_COLLECTION", "playwright_docs")
