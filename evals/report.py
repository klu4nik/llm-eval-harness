"""Per-metric results as JSON lines in reports/, plus a summary.

Every verdict is kept with the judge's reason: stage 6 compares these against
manual labels, and stage 7 compares two runs.

    python -m evals.report reports/deepeval-<run>.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class MetricRecord:
    run_id: str
    case_id: str
    category: str
    metric: str
    score: float | None
    threshold: float
    passed: bool
    reason: str | None
    sut_model: str
    judge_model: str
    error: str | None = None


class ResultLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: MetricRecord) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def read_records(path: Path) -> list[MetricRecord]:
    return [MetricRecord(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line]


def summarize(records: list[MetricRecord]) -> dict[str, dict[str, float]]:
    """Per metric: number of cases, pass rate, mean score (errors count as failures, excluded from the mean)."""
    by_metric: dict[str, list[MetricRecord]] = defaultdict(list)
    for r in records:
        by_metric[r.metric].append(r)
    summary = {}
    for metric, rows in sorted(by_metric.items()):
        scores = [r.score for r in rows if r.score is not None]
        summary[metric] = {
            "cases": len(rows),
            "pass_rate": sum(r.passed for r in rows) / len(rows),
            "mean_score": sum(scores) / len(scores) if scores else float("nan"),
            "errors": sum(r.error is not None for r in rows),
        }
    return summary


def format_summary(summary: dict[str, dict[str, float]]) -> str:
    lines = [f"{'metric':<22}{'cases':>6}{'pass':>8}{'mean':>8}{'errors':>8}"]
    for metric, s in summary.items():
        lines.append(
            f"{metric:<22}{s['cases']:>6}{s['pass_rate']:>8.0%}{s['mean_score']:>8.2f}{s['errors']:>8}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_summary(summarize(read_records(Path(sys.argv[1])))))
