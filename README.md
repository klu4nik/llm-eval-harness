# llm-eval-harness

A QA harness for evaluating a RAG chatbot. The system under test answers
questions about **Playwright for Python**, using a pinned snapshot of the
official docs. The harness checks the answers for correctness, grounding,
retrieval quality and robustness.

> Status: **Stage 1 of 8** — the bot, the corpus, the first 12 golden cases, and offline tests.
> DeepEval metrics, robustness tests and judge calibration come next (see [STRATEGY.md](STRATEGY.md)).

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

## Quick start (local, Ollama)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

ollama pull nomic-embed-text
ollama pull llama3.1:8b

python -m app.cli index
python -m app.cli ask "How do I wait for a file download?"
pytest                      # all tests, including the Ollama smoke
pytest -m "not llm"         # offline only, same as CI
```

Settings are environment variables (see `app/config.py`): `LLM_MODEL`, `EMBED_MODEL`, `TOP_K`, `CHUNK_MAX_CHARS`, `OLLAMA_HOST`.

## Tests so far

| Suite | Needs a model | What it checks |
| --- | --- | --- |
| `tests/unit` | no | preprocessing rules, chunking (no code fence split, unique ids, no leaked JS/Java/C#), bot wiring with a fake LLM |
| `tests/dataset` | no | the golden set itself: schema, category coverage, expected sources exist in the corpus, `must_mention` terms are present in those sources |
| `tests/smoke` (`-m llm`) | yes | one answerable question and one out-of-scope refusal against the real model |

## Golden set

`data/golden_set.json`: 12 cases for now. Categories: `factual`, `multi_hop`, `paraphrase`, `typo`, `out_of_scope`.
Each case has an expected answer, `must_mention` terms, expected `(doc, section)` sources and a `should_refuse` flag.

## Corpus

Pages from [microsoft/playwright](https://github.com/microsoft/playwright) `docs/src`, pinned to commit
`afa6836a`, Apache License 2.0. To refresh: `python -m scripts.fetch_corpus`, then re-check the golden set (`pytest tests/dataset`).
