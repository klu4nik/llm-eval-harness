"""Golden case + bot response -> DeepEval test case."""

from __future__ import annotations

from deepeval.test_case import LLMTestCase

from app.bot import BotResponse
from app.golden import GoldenCase

# One case per category: enough to see that the judged pipeline works, cheap enough to run often.
SMOKE_CASES = ("GS-001", "GS-008", "GS-010", "GS-011", "GS-012")


def select_cases(cases: list[GoldenCase], spec: str) -> list[GoldenCase]:
    """`all`, `smoke`, or a comma-separated list of case ids."""
    if spec == "all":
        return cases
    wanted = SMOKE_CASES if spec == "smoke" else tuple(i.strip() for i in spec.split(",") if i.strip())
    known = {c.id for c in cases}
    unknown = [i for i in wanted if i not in known]
    if unknown:
        raise ValueError(f"unknown golden case ids: {unknown}")
    return [c for c in cases if c.id in wanted]


def to_llm_test_case(case: GoldenCase, response: BotResponse) -> LLMTestCase:
    return LLMTestCase(
        name=case.id,
        input=case.question,
        actual_output=response.answer,
        expected_output=case.expected_answer,
        retrieval_context=response.context_texts,
        completion_time=response.latency_ms / 1000,
        tags=[case.category],
        metadata={
            "case_id": case.id,
            "category": case.category,
            "model": response.model,
            "refused": response.refused,
            "retrieved": [c.chunk_id for c in response.contexts],
        },
    )
