"""LLM-judged metrics (DeepEval) over the golden set.

Needs Ollama with the bot model, the judge model (JUDGE_MODEL) and the index.
Parametrized in conftest.py from --eval-cases (default: smoke subset).

    pytest tests/eval --eval-cases=smoke
    pytest tests/eval --eval-cases=all
    pytest tests/eval --eval-cases=GS-004,GS-011
"""

import pytest

from app.config import Settings
from evals.cases import to_llm_test_case
from evals.metrics import build_metric
from evals.report import MetricRecord

pytestmark = [pytest.mark.llm, pytest.mark.judge]


def test_metric(judged, ask, judge, result_log, run_id):
    case, metric_name = judged
    response = ask(case)
    metric = build_metric(metric_name, judge)
    error = None
    try:
        metric.measure(to_llm_test_case(case, response))
    except Exception as exc:  # usually the judge returned JSON that does not match the schema
        error = f"{type(exc).__name__}: {exc}"
    passed = error is None and metric.is_successful()
    result_log.write(
        MetricRecord(
            run_id=run_id,
            case_id=case.id,
            category=case.category,
            metric=metric_name,
            score=None if error else metric.score,
            threshold=metric.threshold,
            passed=passed,
            reason=None if error else metric.reason,
            sut_model=response.model,
            judge_model=Settings().judge_model,
            error=error,
        )
    )
    assert error is None, f"judge failed: {error}"
    assert passed, f"{metric_name} = {metric.score:.2f} < {metric.threshold}\nanswer: {response.answer}\nreason: {metric.reason}"


def test_out_of_scope_is_refused(refusal_case, ask):
    """Refusal is a fixed string, so no judge is needed."""
    response = ask(refusal_case)
    assert response.refused, f"expected a refusal, got: {response.answer}"
