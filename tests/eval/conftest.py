from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.config import ROOT, Settings
from app.golden import load_golden_set
from evals.cases import select_cases
from evals.judge import build_judge
from evals.metrics import metric_names_for
from evals.report import ResultLog, format_summary, read_records, summarize
from tests.conftest import ollama_or_skip

_RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
_LOG_PATH = ROOT / "reports" / f"deepeval-{_RUN_ID}.jsonl"


def pytest_generate_tests(metafunc):
    """Parametrize over the cases picked with --eval-cases: one test per (case, metric), one per refusal case."""
    cases = select_cases(load_golden_set(), metafunc.config.getoption("--eval-cases"))
    if "judged" in metafunc.fixturenames:
        pairs = [(c, m) for c in cases for m in metric_names_for(c)]
        metafunc.parametrize("judged", pairs, ids=[f"{c.id}-{m}" for c, m in pairs])
    if "refusal_case" in metafunc.fixturenames:
        refusals = [c for c in cases if c.should_refuse]
        metafunc.parametrize("refusal_case", refusals, ids=[c.id for c in refusals])


@pytest.fixture(scope="session")
def judge():
    settings = Settings()
    ollama_or_skip(settings.judge_host, settings.judge_model)
    return build_judge(settings)


@pytest.fixture(scope="session")
def ask(real_bot):
    """Ask each question once per session: all metrics of a case judge the same answer."""
    cache = {}

    def _ask(case):
        if case.id not in cache:
            cache[case.id] = real_bot.ask(case.question)
        return cache[case.id]

    return _ask


@pytest.fixture(scope="session")
def result_log() -> ResultLog:
    return ResultLog(_LOG_PATH)


@pytest.fixture(scope="session")
def run_id() -> str:
    return _RUN_ID


def pytest_terminal_summary(terminalreporter):
    if _LOG_PATH.exists():
        terminalreporter.section("DeepEval summary")
        terminalreporter.write_line(format_summary(summarize(read_records(_LOG_PATH))))
        terminalreporter.write_line(f"details: {_LOG_PATH.relative_to(ROOT)}")
