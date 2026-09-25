"""Which DeepEval metrics run on which golden case, and with what thresholds.

Refusal cases get no judged metrics: "did it refuse?" is a string check
(REFUSAL_TEXT), and faithfulness/relevancy of a refusal says nothing useful.

Thresholds are starting points. Stage 6 (judge calibration) will set them from
manual labels instead of intuition.
"""

from __future__ import annotations

from typing import Callable

from deepeval.metrics import (
    AnswerRelevancyMetric,
    BaseMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.models import DeepEvalBaseLLM
from deepeval.test_case import SingleTurnParams

from app.golden import GoldenCase

THRESHOLDS = {
    "faithfulness": 0.8,  # risk #1: hallucination
    "answer_relevancy": 0.7,
    "contextual_precision": 0.5,  # risk #2: are the right chunks ranked first?
    "contextual_recall": 0.7,  # risk #2: does the context hold everything the expected answer needs?
    "correctness": 0.6,
}

CORRECTNESS_STEPS = [
    "Compare the facts in 'actual output' with the facts in 'expected output'.",
    "Heavily penalize any statement in 'actual output' that contradicts 'expected output'.",
    "Penalize key facts from 'expected output' that are missing in 'actual output'.",
    "Do not penalize extra details or different wording, as long as they do not contradict 'expected output'.",
    "Penalize code or API names that are not Playwright's Python API (snake_case), e.g. JavaScript camelCase.",
]


def _correctness(judge: DeepEvalBaseLLM) -> BaseMetric:
    return GEval(
        name="Correctness",
        evaluation_steps=CORRECTNESS_STEPS,
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=THRESHOLDS["correctness"],
        model=judge,
        async_mode=False,
    )


# async_mode=False: a local Ollama serves one request at a time anyway, and sequential calls keep logs readable.
_FACTORIES: dict[str, Callable[[DeepEvalBaseLLM], BaseMetric]] = {
    "faithfulness": lambda j: FaithfulnessMetric(THRESHOLDS["faithfulness"], model=j, async_mode=False),
    "answer_relevancy": lambda j: AnswerRelevancyMetric(THRESHOLDS["answer_relevancy"], model=j, async_mode=False),
    "contextual_precision": lambda j: ContextualPrecisionMetric(
        THRESHOLDS["contextual_precision"], model=j, async_mode=False
    ),
    "contextual_recall": lambda j: ContextualRecallMetric(THRESHOLDS["contextual_recall"], model=j, async_mode=False),
    "correctness": _correctness,
}

METRIC_NAMES = tuple(_FACTORIES)


def metric_names_for(case: GoldenCase) -> tuple[str, ...]:
    return () if case.should_refuse else METRIC_NAMES


def build_metric(name: str, judge: DeepEvalBaseLLM) -> BaseMetric:
    return _FACTORIES[name](judge)
