# Dashboard browser smoke

Run from this directory with Node.js 20+ and Python 3.10+:

```sh
npm ci
npx playwright install --with-deps chromium
npm test
```

The suite opens the production product center and `/products/:entryId` details
through the real `CenterServer`, `CenterCatalog` and `CenterStore`. Each test gets
disposable records, center state and an OS-assigned loopback port. The shared
`fixtures.js` starts `center-fixture-server.py`; `journal.spec.js` creates richer
archive records served by `fixture-server.py` through the same center stack.
Execution adapters are fake and model preparation/dispatch never runs. The
framework root is used only to read the actual application and documentation.

| Previous standalone coverage | Center-only coverage |
| --- | --- |
| Journal refresh, bootstrap and save errors | Entry-scoped journal recovery and center preference save/reload |
| Standalone language/current-product controls | Center language preference reflected in both views; product language remains a separate preference |
| Optional backup, host Start/Stop and global consensus | Legacy page redirects, retired global API rejection and four working docs links in both settings dialogs |
| History, dates, logs, usage, identity and resource safety | Existing detail regressions use entry/source-scoped APIs, real imports and original records |

Standalone host-control tests were retired with that interface. Center queue,
stop, ownership, confirmation and request-race regressions remain in
`center.spec.js` and `dashboard-b.spec.js`. Journal tests retain continuous and
exploration history, unknown usage, source-bound logs and documents, identity
relocation/replacement, unsafe report text, keyboard focus, breakpoints and
failure recovery. Synthetic response tests preserve the center response envelope
and pagination contract; normal requests use the real server.

Product-center regressions also cover six-round history and usage, older recorded
details, optional exploration directions, preparation failures after reload,
owned attention stop controls, and refresh focus. Their isolated center uses real
catalog and HTTP handlers with a fake execution adapter; the clone worker and
preview health are injected. These fixtures do not verify a live model or preview
process and are not product showcase screenshots.

Center race regressions hold HTTP responses while users close or reopen shared
Radix dialogs, edit settings, switch sources, or replace import candidates. They
also verify incomplete refresh freshness, retry focus and nested dialog return
focus. New-work tests use the current batch form and endpoint. Fixture screenshots
are saved through each test's output path, never into historical acceptance folders.

Python defaults to `python` on Windows and `python3` elsewhere. Set
`AUTONOMOUS_COMPANY_BROWSER_PYTHON` to an executable path if needed. Tests run serially
without automatic retries. Failures retain screenshots, traces and server logs
under `test-results/`; the HTML report is in `playwright-report/`. CI should upload
both directories on failure.

`showcase.spec.js` serves the public snapshots from `examples/`, checks the 22-entry
catalog and CLI entrypoint, loads every static frontend and exercises the migrated
CSV/SRT examples, text counter, editable decision link and Chinese scope sheet.
Backend entrypoints are checked for presence; their domain tests remain in each
example and are not substituted by this static-browser smoke suite.
