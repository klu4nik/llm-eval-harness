# llm-eval-harness

A QA harness for evaluating a RAG chatbot. The system under test answers
questions about **Playwright for Python**, using a pinned snapshot of the
official docs. The harness checks the answers for correctness, grounding,
retrieval quality and robustness.

> Status: **Stages 1 and 4 of 8** — the bot, the corpus, the first 12 golden cases, offline tests, and LLM-judged DeepEval metrics.
> Deterministic checks, robustness tests and judge calibration come next (see [STRATEGY.md](STRATEGY.md)).

## Architecture

```
data/corpus/*.md ──► chunker ──► Ollama embeddings ──► ChromaDB (.index/)
                                                          │ top-k
question ─────────────────────────────────────────────► retriever ──► prompt ──► Ollama LLM ──► BotResponse
                                                                                              (answer, contexts,
                                                                                               latency, refused)
```

- `app/preprocess.py`: turns the multi-language upstream docs into Python-only Markdown (drops JS/Java/C# code and language-specific sections, rewrites API refs to snake_case).
- `app/chunker.py`: heading-aware chunks. Each chunk has `(doc, section)` metadata, and the golden set points to that, not to chunk ids, so changing the chunk size does not invalidate it.
- `app/bot.py`: `RagBot.ask()` returns the answer **together with** the retrieved contexts. The eval layer needs the contexts for faithfulness and retrieval metrics.
- `app/llm.py`: `Embedder` / `ChatModel` protocols, so tests can use fakes and run in CI without a model.
- `evals/`: the DeepEval layer. `cases.py` maps a golden case + `BotResponse` to an `LLMTestCase`, `metrics.py` picks metrics and thresholds per case, `judge.py` builds the local Ollama judge, `report.py` logs every verdict with the judge's reason.

## Quick start (local, Ollama)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

ollama pull nomic-embed-text
ollama pull llama3.1:8b
ollama pull qwen2.5:7b          # judge for the DeepEval metrics

python -m app.cli index
python -m app.cli ask "How do I wait for a file download?"
pytest                      # all tests, including the Ollama smoke
pytest -m "not llm"         # offline only, same as CI
pytest tests/eval                       # DeepEval metrics, smoke subset (one case per category)
pytest tests/eval --eval-cases=all      # whole golden set
pytest tests/eval --eval-cases=GS-004   # selected cases
python -m evals.report reports/deepeval-<run>.jsonl   # summary of a past run
```

Settings are environment variables (see `app/config.py`): `LLM_MODEL`, `EMBED_MODEL`, `TOP_K`, `CHUNK_MAX_CHARS`, `OLLAMA_HOST`, `JUDGE_MODEL`, `JUDGE_HOST`.

## Tests so far

| Suite | Needs a model | What it checks |
| --- | --- | --- |
| `tests/unit` | no | preprocessing rules, chunking (no code fence split, unique ids, no leaked JS/Java/C#), bot wiring with a fake LLM |
| `tests/dataset` | no | the golden set itself: schema, category coverage, expected sources exist in the corpus, `must_mention` terms are present in those sources |
| `tests/smoke` (`-m llm`) | yes | one answerable question and one out-of-scope refusal against the real model |
| `tests/eval` (`-m judge`) | yes + judge | DeepEval per case: faithfulness, answer relevancy, contextual precision, contextual recall, GEval correctness vs the expected answer; refusal cases checked by string. Results go to `reports/deepeval-<run>.jsonl` |

`tests/unit/test_evals.py` covers the DeepEval glue in CI: every metric runs end to end against a scripted judge, so a DeepEval upgrade that breaks the wiring fails offline.

## DeepEval metrics

| Metric | Risk it covers | Threshold |
| --- | --- | --- |
| Faithfulness | hallucination: claims not supported by the retrieved context | 0.8 |
| Answer relevancy | answer drifts away from the question | 0.7 |
| Contextual precision | relevant chunks are not ranked first | 0.5 |
| Contextual recall | the context lacks facts the expected answer needs | 0.7 |
| Correctness (GEval) | answer contradicts or misses the expected answer, or uses a non-Python API | 0.6 |

Thresholds are starting points; stage 6 sets them from manual labels. Out-of-scope cases get no judged metric: the refusal is a fixed string.

## Golden set

`data/golden_set.json`: 12 cases for now. Categories: `factual`, `multi_hop`, `paraphrase`, `typo`, `out_of_scope`.
Each case has an expected answer, `must_mention` terms, expected `(doc, section)` sources and a `should_refuse` flag.

## Corpus

Pages from [microsoft/playwright](https://github.com/microsoft/playwright) `docs/src`, pinned to commit
`afa6836a`, Apache License 2.0. To refresh: `python -m scripts.fetch_corpus`, then re-check the golden set (`pytest tests/dataset`).
