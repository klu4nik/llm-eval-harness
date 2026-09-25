"""Command line entry point.

    python -m app.cli index                 # embed the corpus into .index/
    python -m app.cli ask "How do I ..."    # ask one question, show answer + sources
"""

from __future__ import annotations

import argparse

from app.config import Settings
from app.factory import build_bot, build_index


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="build the vector index from data/corpus")
    ask = sub.add_parser("ask", help="ask the bot a question")
    ask.add_argument("question")
    args = parser.parse_args()

    settings = Settings()
    if args.command == "index":
        print(f"indexed {build_index(settings)} chunks with {settings.embed_model}")
        return

    response = build_bot(settings).ask(args.question)
    print(response.answer)
    print(f"\n--- {response.model}, {response.latency_ms:.0f} ms, refused={response.refused}")
    for n, c in enumerate(response.contexts, start=1):
        print(f"[{n}] {c.chunk_id}  score={c.score:.3f}")


if __name__ == "__main__":
    main()
