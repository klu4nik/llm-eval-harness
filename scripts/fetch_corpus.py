"""Download the pinned Playwright doc pages and save Python-only versions to data/corpus/.

Usage: python -m scripts.fetch_corpus
"""

from __future__ import annotations

import urllib.request

from app.config import CORPUS_DIR, PLAYWRIGHT_DOCS, PLAYWRIGHT_DOCS_COMMIT
from app.preprocess import to_python_markdown

RAW_URL = "https://raw.githubusercontent.com/microsoft/playwright/{commit}/docs/src/{name}.md"


def main() -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for name in PLAYWRIGHT_DOCS:
        url = RAW_URL.format(commit=PLAYWRIGHT_DOCS_COMMIT, name=name)
        with urllib.request.urlopen(url, timeout=30) as resp:
            source = resp.read().decode("utf-8")
        target = CORPUS_DIR / f"{name}.md"
        target.write_text(to_python_markdown(source), encoding="utf-8")
        print(f"saved {target.relative_to(CORPUS_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
