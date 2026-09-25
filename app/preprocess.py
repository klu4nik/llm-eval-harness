"""Turn Playwright's multi-language doc sources into Python-only Markdown.

The upstream docs (microsoft/playwright, docs/src) hold JS, Java, C# and Python
in one file. Leaving other languages in the corpus would let the bot answer a
Python question with JS code, so we strip them before indexing:

* code fences are kept only for Python (sync API), shell and neutral formats;
* sections marked ``* langs: ...`` without ``python`` are dropped;
* API references like [`method: Page.getByRole`] become ``page.get_by_role``.
"""

from __future__ import annotations

import re

KEEP_FENCE_LANGS = {"python", "py", "bash", "sh", "html", "txt", "ini", "json", ""}
DROP_TAB_PREFIXES = ("bash-powershell", "bash-batch")

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_LANGS = re.compile(r"^\*{1,2}\s*langs:\s*(.+)$")
_API_REF = re.compile(r"\[`(method|event|option|property):\s*([^`]+)`\](\([^)]*\))?")
_CLASS_REF = re.compile(r"\[([A-Z][A-Za-z]+)\](?!\()")
# Docusaurus-only markup that carries no content for a text-only bot.
_JSX_LINE = re.compile(r"^\s*(</?(Tabs|TabItem|LiteYouTube|img)\b.*|import \w+ from '@site/.*)$")


def camel_to_snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def _api_ref_to_python(kind: str, ref: str) -> str:
    parts = ref.strip().split(".")
    if kind == "event" and len(parts) == 2:
        return f'`{parts[0][0].lower() + parts[0][1:]}.on("{parts[1]}")`'
    if kind == "option":
        return f"`{camel_to_snake(parts[-1])}`"
    owner = camel_to_snake(parts[0])
    member = camel_to_snake(parts[-1])
    return f"`{owner}.{member}`"


def rewrite_refs(line: str) -> str:
    line = _API_REF.sub(lambda m: _api_ref_to_python(m.group(1), m.group(2)), line)
    return _CLASS_REF.sub(r"\1", line)


def keep_fence(info: str) -> bool:
    """Decide from a fence info string (```python sync / ```js tab=...) whether to keep the block."""
    tokens = info.split()
    lang = tokens[0] if tokens else ""
    attrs = tokens[1:]
    if lang not in KEEP_FENCE_LANGS:
        return False
    if lang in ("python", "py") and "async" in attrs:
        return False  # keep the sync API only, avoids near-duplicate chunks
    for attr in attrs:
        if attr.startswith("tab=") and attr[4:].startswith(DROP_TAB_PREFIXES):
            return False
        if attr.startswith("lang=") and attr[5:] != "python":
            return False
    # "```bash js" / "```bash java": second token names a language that is not python
    if lang == "bash" and attrs and "=" not in attrs[0] and attrs[0] != "python":
        return False
    return True


def to_python_markdown(source: str) -> str:
    lines = source.splitlines()
    out: list[str] = []
    in_fence = False
    keep_current_fence = True
    skip_level: int | None = None  # heading level of a section dropped by `* langs:`
    pending_heading: tuple[int, str] | None = None

    i = 0
    if lines and lines[0].strip() == "---":  # front matter: keep only the title
        end = lines.index("---", 1)
        for fm in lines[1:end]:
            if fm.startswith("title:"):
                out.append("# " + fm.split(":", 1)[1].strip().strip('"'))
        i = end + 1

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                keep_current_fence = keep_fence(stripped[3:].strip())
            else:
                in_fence = False
            if skip_level is None and keep_current_fence:
                out.append(line)
            i += 1
            continue

        if in_fence:
            if skip_level is None and keep_current_fence:
                out.append(line)
            i += 1
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None:
                pending_heading = (level, line)
                out.append(rewrite_refs(line))
            i += 1
            continue

        langs = _LANGS.match(stripped)
        if langs:
            allowed = {x.strip() for x in langs.group(1).split(",")}
            if "python" not in allowed and skip_level is None and pending_heading:
                level, heading_line = pending_heading
                # remove the heading we already emitted
                while out and out[-1] != rewrite_refs(heading_line):
                    out.pop()
                if out:
                    out.pop()
                skip_level = level
            i += 1
            continue

        if skip_level is None and not _JSX_LINE.match(line):
            out.append(rewrite_refs(line))
        i += 1

    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"
