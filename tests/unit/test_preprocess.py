import pytest

from app.preprocess import camel_to_snake, keep_fence, rewrite_refs, to_python_markdown


@pytest.mark.parametrize(
    "info, expected",
    [
        ("python sync", True),
        ("python async", False),
        ("py title=\"conftest.py\"", True),
        ("js", False),
        ("java", False),
        ("csharp title=\"UnitTest1.cs\"", False),
        ("bash", True),
        ("bash python", True),
        ("bash js", False),
        ("bash lang=csharp", False),
        ("powershell tab=bash-powershell", False),
        ("html card", True),
    ],
)
def test_keep_fence(info, expected):
    assert keep_fence(info) is expected


@pytest.mark.parametrize(
    "line, expected",
    [
        ("[`method: Page.getByRole`](#locate-by-role)", "`page.get_by_role`"),
        ("[`method: LocatorAssertions.toBeVisible`]", "`locator_assertions.to_be_visible`"),
        ("[`event: Page.dialog`] listener", '`page.on("dialog")` listener'),
        ("the [`option: BrowserType.launch.downloadsPath`] option", "the `downloads_path` option"),
        ("using the [Download] object", "using the Download object"),
    ],
)
def test_rewrite_refs(line, expected):
    assert rewrite_refs(line) == expected


def test_camel_to_snake():
    assert camel_to_snake("getByTestId") == "get_by_test_id"


SOURCE = """---
id: demo
title: "Demo page"
---

## Shared

Text for everyone.

```js
await page.click();
```

```python sync
page.click()
```

```python async
await page.click()
```

## JS only
* langs: js

Only for JS.

### Nested JS detail

Still JS.

## Python only
* langs: python

Python text.
"""


def test_to_python_markdown_keeps_only_python():
    out = to_python_markdown(SOURCE)
    assert out.startswith("# Demo page")
    assert "page.click()" in out
    assert "await" not in out
    assert "JS only" not in out and "Still JS" not in out
    assert "## Python only" in out and "Python text." in out
    assert "langs:" not in out
