from app.chunker import chunk_document, split_sections

DOC = """# Dialogs

Intro text.

## Handling

Register a handler.

```python sync
# a comment that looks like a heading
page.on("dialog", lambda d: d.accept())
```

### Details

More details.
"""


def test_sections_ignore_headings_inside_code():
    sections = split_sections("dialogs", DOC)
    assert [s.heading for s in sections] == ["Introduction", "Handling", "Details"]
    assert all(s.title == "Dialogs" for s in sections)


def test_chunk_text_has_breadcrumb_and_metadata():
    chunks = chunk_document("dialogs", DOC)
    handling = next(c for c in chunks if c.section == "Handling")
    assert handling.text.startswith("Dialogs > Handling")
    assert handling.chunk_id == "dialogs#handling-0"
    assert "d.accept()" in handling.text


def test_long_section_is_split_without_breaking_code():
    body = "\n\n".join(f"Paragraph {i} " + "x" * 80 for i in range(20))
    code = "```python\n" + "\n\n".join(f"line_{i} = {i}" for i in range(10)) + "\n```"
    chunks = chunk_document("doc", f"# T\n\n## Long\n\n{body}\n\n{code}", max_chars=400)
    assert len(chunks) > 1
    for c in chunks:
        assert c.text.count("```") % 2 == 0, f"code fence split in {c.chunk_id}"
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_corpus_chunk_ids_are_unique(corpus_chunks):
    ids = [c.chunk_id for c in corpus_chunks]
    assert len(ids) == len(set(ids))


def test_corpus_has_no_other_languages(corpus_chunks):
    leaked = [c.chunk_id for c in corpus_chunks if "```js" in c.text or "```java" in c.text or "```csharp" in c.text]
    assert not leaked
