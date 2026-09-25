"""The judge model used by DeepEval metrics.

Local Ollama by default, same determinism settings as the bot (temperature 0,
fixed seed), so judge noise stays measurable in stage 6.
"""

from __future__ import annotations

from deepeval.models import DeepEvalBaseLLM, OllamaModel

from app.config import Settings


def build_judge(settings: Settings | None = None) -> DeepEvalBaseLLM:
    settings = settings or Settings()
    return OllamaModel(
        model=settings.judge_model,
        base_url=settings.judge_host,
        temperature=0,
        generation_kwargs={"seed": settings.seed},
    )
