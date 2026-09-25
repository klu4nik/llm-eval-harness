"""LLM-judged evaluation (DeepEval) of the RAG bot against the golden set."""

import os

# DeepEval reads these at import time: no telemetry, no update check on every run.
os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")
os.environ.setdefault("DEEPEVAL_UPDATE_WARNING_OPT_IN", "NO")
