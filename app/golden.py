"""Golden set loader. Shared by dataset checks now and by the eval suites later."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import GOLDEN_SET

CATEGORIES = {"factual", "multi_hop", "paraphrase", "typo", "out_of_scope"}


@dataclass(frozen=True)
class SourceRef:
    doc: str
    section: str


@dataclass(frozen=True)
class GoldenCase:
    id: str
    category: str
    question: str
    expected_answer: str
    must_mention: tuple[str, ...]
    expected_sources: tuple[SourceRef, ...]
    should_refuse: bool
    paraphrase_of: str | None = None


def load_golden_set(path: Path = GOLDEN_SET) -> list[GoldenCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        GoldenCase(
            id=c["id"],
            category=c["category"],
            question=c["question"],
            expected_answer=c["expected_answer"],
            must_mention=tuple(c["must_mention"]),
            expected_sources=tuple(SourceRef(**s) for s in c["expected_sources"]),
            should_refuse=c["should_refuse"],
            paraphrase_of=c.get("paraphrase_of"),
        )
        for c in raw["cases"]
    ]
