# Trace viewer

## Opening Trace Viewer

You can open a saved trace using either the Playwright CLI or in the browser at [trace.playwright.dev](https://trace.playwright.dev). Make sure to add the full path to where your `trace.zip` file is located.

```bash python
playwright show-trace trace.zip
```

### Using [trace.playwright.dev](https://trace.playwright.dev)

[trace.playwright.dev](https://trace.playwright.dev) is a statically hosted variant of the Trace Viewer. You can upload a trace file using drag and drop or via the `Select file` button.

Trace Viewer loads the trace entirely in your browser and does not transmit any data externally.

### Viewing remote traces

You can open remote traces directly using its URL. This makes it easy to view the remote trace without having to manually download the file from CI runs, for example.

```bash python
playwright show-trace https://example.com/trace.zip
```

When using [trace.playwright.dev](https://trace.playwright.dev), you can also pass the URL of your uploaded trace at some accessible storage (e.g. inside your CI) as a query parameter. CORS (Cross-Origin Resource Sharing) rules might apply.

```txt
https://trace.playwright.dev/?trace=https://demo.playwright.dev/reports/todomvc/data/e6099cadf79aa753d5500aa9508f9d1dbd87b5ee.zip
```

## Recording a trace

Traces can be recorded by running your tests with the `--tracing` flag.

```bash
pytest --tracing on
```
Options for tracing are:
- `on`: Record trace for each test
- `off`: Do not record trace. (default)
- `retain-on-failure`: Record trace for each test, but remove all traces from successful test runs.

This will record the trace and place it into the file named `trace.zip` in your `test-results` directory.

<details>
<summary>If you are not using Pytest, click here to learn how to record traces.</summary>

```python sync
browser = chromium.launch()
context = browser.new_context()

# Start tracing before creating / navigating a page.
context.tracing.start(screenshots=True, snapshots=True, sources=True)

page = context.new_page()
page.goto("https://playwright.dev")

# Stop tracing and export it into a zip archive.
context.tracing.stop(path = "trace.zip")
```

</details>

## Trace Viewer features
### Actions

In the Actions tab you can see what locator was used for every action and how long each one took to run. Hover over each action of your test and visually see the change in the DOM snapshot. Go back and forward in time and click an action to inspect and debug. Use the Before and After tabs to visually see what happened before and after the action.

**Selecting each action reveals:**
- Action snapshots
- Action log
- Source code location

### Screenshots

When tracing with the `screenshots` option turned on (default), each trace records a screencast and renders it as a film strip. You can hover over the film strip to see a magnified image of for each action and state which helps you easily find the action you want to inspect.

Double click on an action to see the time range for that action. You can use the slider in the timeline to increase the actions selected and these will be shown in the Actions tab and all console logs and network logs will be filtered to only show the logs for the actions selected.

### Snapshots

When tracing with the `snapshots` option turned on (default), Playwright captures a set of complete DOM snapshots for each action. Depending on the type of the action, it will capture:

| Type | Description |
|------|-------------|
|Before|A snapshot at the time action is called.|
|Action|A snapshot at the moment of the performed input. This type of snapshot is especially useful when exploring where exactly Playwright clicked.|
|After|A snapshot after the action.|

Here is what the typical Action snapshot looks like:

Notice how it highlights both, the DOM Node as well as the exact click position.

### Source

When you click on an action in the sidebar, the line of code for that action is highlighted in the source panel.

### Call

The call tab shows you information about the action such as the time it took, what locator was used, if in strict mode and what key was used.

### Log

See a full log of your test to better understand what Playwright is doing behind the scenes such as scrolling into view, waiting for element to be visible, enabled and stable and performing actions such as click, fill, press etc.

### Errors

If your test fails you will see the error messages for each test in the Errors tab. The timeline will also show a red line highlighting where the error occurred. You can also click on the source tab to see on which line of the source code the error is.

### Console

See console logs from the browser as well as from your test. Different icons are displayed to show you if the console log came from the browser or from the test file.

Double click on an action from your test in the actions sidebar. This will filter the console to only show the logs that were made during that action. Click the *Show all* button to see all console logs again.

Use the timeline to filter actions, by clicking a start point and dragging to an ending point. The console tab will also be filtered to only show the logs that were made during the actions selected.

### Network

The Network tab shows you all the network requests that were made during your test. You can sort by different types of requests, status code, method, request, content type, duration and size. Click on a request to see more information about it such as the request headers, response headers, request body and response body.

Double click on an action from your test in the actions sidebar. This will filter the network requests to only show the requests that were made during that action. Click the *Show all* button to see all network requests again.

Use the timeline to filter actions, by clicking a start point and dragging to an ending point. The network tab will also be filtered to only show the network requests that were made during the actions selected.

### Metadata

Next to the Actions tab you will find the Metadata tab which will show you more information on your test such as the Browser, viewport size, test duration and more.
