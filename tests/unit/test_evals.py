"""The DeepEval glue without a real judge: case selection, test case mapping, metric wiring, report summary."""

import types
import typing

import pytest
from deepeval.models import DeepEvalBaseLLM
from pydantic import BaseModel

from app.bot import RagBot
from app.config import Settings
from evals.cases import SMOKE_CASES, select_cases, to_llm_test_case
from evals.judge import build_judge
from evals.metrics import METRIC_NAMES, THRESHOLDS, build_metric, metric_names_for
from evals.report import MetricRecord, ResultLog, read_records, summarize


class NoCallJudge(DeepEvalBaseLLM):
    """Building a metric must not call the judge."""

    def __init__(self):
        super().__init__("no-call-judge")

    def load_model(self):
        return None

    def generate(self, prompt, schema=None):
        raise AssertionError("judge called")

    async def a_generate(self, prompt, schema=None):
        raise AssertionError("judge called")

    def get_model_name(self):
        return "no-call-judge"


def _fill(tp):
    """A schema-valid value for any pydantic judge schema: every verdict "yes", every score high."""
    origin = typing.get_origin(tp)
    if origin in (typing.Union, types.UnionType):
        return _fill(next(a for a in typing.get_args(tp) if a is not type(None)))
    if origin is list:
        return [_fill(typing.get_args(tp)[0])]
    if origin is typing.Literal:
        return typing.get_args(tp)[0]
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return tp(**{n: "yes" if n == "verdict" else _fill(f.annotation) for n, f in tp.model_fields.items()})
    return {str: "yes", int: 8, float: 8.0, bool: True}.get(tp)


class ScriptedJudge(NoCallJudge):
    """Answers every judge prompt with an all-positive, schema-valid object."""

    def generate(self, prompt, schema=None):
        return _fill(schema) if schema else "yes"

    async def a_generate(self, prompt, schema=None):
        return self.generate(prompt, schema)


def test_smoke_subset_covers_every_category(golden_set):
    assert {c.category for c in select_cases(golden_set, "smoke")} == {c.category for c in golden_set}
    assert len(select_cases(golden_set, "smoke")) == len(SMOKE_CASES)


def test_select_by_ids_and_all(golden_set):
    assert [c.id for c in select_cases(golden_set, "GS-004, GS-002")] == ["GS-002", "GS-004"]
    assert select_cases(golden_set, "all") == golden_set


def test_unknown_case_id_is_an_error(golden_set):
    with pytest.raises(ValueError, match="GS-999"):
        select_cases(golden_set, "GS-001,GS-999")


def test_refusal_cases_get_no_judged_metrics(golden_set):
    for case in golden_set:
        assert metric_names_for(case) == (() if case.should_refuse else METRIC_NAMES)


def test_llm_test_case_carries_answer_context_and_expected_answer(golden_set, offline_retriever, fake_llm):
    case = golden_set[0]
    response = RagBot(offline_retriever, fake_llm, top_k=3).ask(case.question)
    tc = to_llm_test_case(case, response)
    assert tc.input == case.question
    assert tc.actual_output == response.answer
    assert tc.expected_output == case.expected_answer
    assert tc.retrieval_context == response.context_texts and len(tc.retrieval_context) == 3
    assert tc.metadata["case_id"] == case.id
    assert tc.metadata["retrieved"] == [c.chunk_id for c in response.contexts]


@pytest.mark.parametrize("name", METRIC_NAMES)
def test_metrics_use_the_given_judge_and_threshold(name):
    metric = build_metric(name, NoCallJudge())
    assert metric.threshold == THRESHOLDS[name]
    assert metric.evaluation_model == "no-call-judge"


def _record(metric, score, passed, error=None):
    return MetricRecord("r1", "GS-001", "factual", metric, score, 0.5, passed, "why", "bot", "judge", error)


def test_report_roundtrip_and_summary(tmp_path):
    log = ResultLog(tmp_path / "run.jsonl")
    for r in [
        _record("faithfulness", 1.0, True),
        _record("faithfulness", 0.4, False),
        _record("faithfulness", None, False, error="ValidationError"),
    ]:
        log.write(r)
    records = read_records(log.path)
    assert records[2].error == "ValidationError"
    s = summarize(records)["faithfulness"]
    assert s["cases"] == 3 and s["errors"] == 1
    assert s["pass_rate"] == pytest.approx(1 / 3)
    assert s["mean_score"] == pytest.approx(0.7)


@pytest.mark.parametrize("name", METRIC_NAMES)
def test_metrics_run_end_to_end_with_a_scripted_judge(name, golden_set, offline_retriever, fake_llm):
    """Catches DeepEval API changes (params, schemas, score/reason) in CI, where no real judge is available."""
    case = golden_set[0]
    metric = build_metric(name, ScriptedJudge())
    metric.measure(to_llm_test_case(case, RagBot(offline_retriever, fake_llm).ask(case.question)))
    assert metric.is_successful()
    assert 0.0 <= metric.score <= 1.0 and metric.reason


def test_judge_is_built_from_settings_without_a_server():
    judge = build_judge(Settings(judge_model="qwen2.5:7b", judge_host="http://judge:11434"))
    assert judge.get_model_name().startswith("qwen2.5:7b")
    assert judge.base_url == "http://judge:11434"
    assert judge.temperature == 0
