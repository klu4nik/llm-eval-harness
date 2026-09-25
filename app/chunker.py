"""Heading-aware chunking.

Each chunk carries its doc id and section heading. The golden set points to
(doc, section), not to chunk ids, so changing CHUNK_MAX_CHARS does not break
the expected sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc: str
    section: str
    text: str


@dataclass
class Section:
    doc: str
    title: str
    heading: str
    body: list[str]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def split_sections(doc: str, markdown: str) -> list[Section]:
    """Split on ## and ### headings (# is the page title). Headings inside code fences are ignored."""
    title = doc
    sections: list[Section] = []
    current = Section(doc, title, "Introduction", [])
    in_fence = False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else _HEADING.match(line)
        if match and len(match.group(1)) == 1:
            title = match.group(2).strip()
            current.title = title
            continue
        if match and len(match.group(1)) in (2, 3):
            if "".join(current.body).strip():
                sections.append(current)
            current = Section(doc, title, match.group(2).strip(), [])
            continue
        current.body.append(line)
    if "".join(current.body).strip():
        sections.append(current)
    return sections


def _split_long(text: str, max_chars: int) -> list[str]:
    """Split on blank lines, never inside a code fence, packing paragraphs up to max_chars."""
    blocks: list[str] = []
    buf: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not line.strip() and not in_fence and buf:
            blocks.append("\n".join(buf))
            buf = []
            continue
        buf.append(line)
    if buf:
        blocks.append("\n".join(buf))

    parts: list[str] = []
    current = ""
    for block in blocks:
        if current and len(current) + len(block) + 2 > max_chars:
            parts.append(current)
            current = block
        else:
            current = f"{current}\n\n{block}" if current else block
    if current:
        parts.append(current)
    return parts


def chunk_document(doc: str, markdown: str, max_chars: int = 1500) -> list[Chunk]:
    chunks: list[Chunk] = []
    seen: dict[str, int] = {}
    for section in split_sections(doc, markdown):
        body = "\n".join(section.body).strip()
        header = f"{section.title} > {section.heading}"
        for part in _split_long(body, max_chars):
            base = f"{doc}#{slugify(section.heading)}"
            n = seen.get(base, 0)
            seen[base] = n + 1
            chunk_id = f"{base}-{n}"
            chunks.append(Chunk(chunk_id, doc, section.heading, f"{header}\n\n{part}"))
    return chunks


def load_corpus(corpus_dir: Path, max_chars: int = 1500) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*.md")):
        chunks.extend(chunk_document(path.stem, path.read_text(encoding="utf-8"), max_chars))
    return chunks
