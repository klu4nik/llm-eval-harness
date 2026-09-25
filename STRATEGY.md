# Test strategy

## What is under test

A RAG bot that answers Playwright (Python) questions from a fixed doc snapshot.
Main risks, from most to least severe:

1. **Hallucination**: the answer states facts or APIs that are not in the retrieved context.
2. **Retrieval miss**: the right section is not in the top-k, so even a perfect generator cannot answer.
3. **Wrong language**: the answer uses JS/Java/C# API instead of Python.
4. **No refusal**: the bot answers out-of-scope questions instead of saying it doesn't know.
5. **Instability**: paraphrased or misspelled questions get different answers.
6. **Prompt injection** through document content.

## Test layers

| Layer | Needs a model | Runs in CI | Stage |
| --- | --- | --- | --- |
| Unit (preprocess, chunker, wiring with fakes) | no | yes | 1 ✅ |
| Dataset validation (golden set checked against the corpus) | no | yes | 1 ✅ |
| Smoke against the real model | yes | no | 1 ✅ |
| Deterministic checks: recall@k, refusal string, Python-only code, latency | embeddings only | partly | 3 |
| LLM-judged metrics (DeepEval): faithfulness, answer relevancy, contextual precision/recall, GEval | yes | wiring only (scripted judge) | 4 ✅ |
| Robustness: paraphrase consistency, typos, prompt injection | yes | no | 5 |
| Judge calibration: manual labels compared with judge verdicts | yes | no | 6 |
| Regression: compare two prompt/model/chunking variants | yes | no | 7 |

## Design decisions

- **Refusal is a fixed string** (`REFUSAL_TEXT`). This makes "did it refuse?" a deterministic check instead of a judge call.
- **Golden sources are `(doc, section)`, not chunk ids.** Chunking is a tuning parameter; the dataset must survive changes to it.
- **The dataset is tested.** A wrong expected answer produces a wrong verdict on every run, so each `must_mention` term must exist in the expected source text.
- **The corpus is pinned** to one upstream commit, so results can be compared across runs.
- **temperature=0, fixed seed** to reduce run-to-run noise. The noise that remains will be measured, not assumed away.
- **The judge is a different model family than the bot** (`qwen2.5:7b` judges `llama3.1:8b`) to limit self-preference bias. A 7B judge is weak, and that is on purpose: stage 6 measures how far to trust it instead of assuming a bigger model is right.
- **One test per (case, metric)**, not one per case. A failure names the metric, and one bad judge output does not hide the other verdicts. The bot is asked once per case per run; all metrics judge the same answer.
- **Every verdict is logged with the judge's reason** (`reports/deepeval-<run>.jsonl`), including judge errors (invalid JSON). Errors count as failures, not as skips: a judge that cannot answer is a finding.
- **Refusal cases are not judged.** Faithfulness of "I don't know" is trivially 1.0 and tells nothing; the fixed refusal string is checked directly.
- **CI cannot run a judge**, so it runs every metric against a scripted judge that returns schema-valid "yes" answers. This checks the wiring and DeepEval API compatibility, not quality.

## Baselines and observations

- Lexical baseline (hashing bag-of-words embedder, top-4): the expected section is retrieved for 7 of 11 answerable cases. The typo case (GS-011) misses completely. This is the floor that real embeddings must beat in stage 3.
- Upstream doc issue: in `test-runners-python.md` → *Fixtures*, the `browser_context_args` marker example asserts that `navigator.userAgent == "Europe/Berlin"` and `languages == ["de-DE"]`, which does not match the `timezone_id` / `locale="en-GB"` it sets. A faithful bot will repeat this example. It's a good case for later: faithfulness passes while correctness fails.
