# Product media runtime

Normal delivery registration and normal cycle finalization automatically capture
supported products. A model does not need to invoke a preview or screenshot tool.
Media failures are diagnostics and do not change checks or AI cycle results.

Node 20+ and Playwright Chromium are optional screenshot dependencies. This uses
the same pinned Playwright version as the Dashboard browser checks, without
requiring a Python browser package or an image-generation model. Install from the
framework root in the **same OS/runtime** that runs the product:

```sh
npm ci --prefix scripts/media
node scripts/media/node_modules/playwright/cli.js install chromium
```

Existing `tests/browser/node_modules/playwright` is also reused when available.
The program never downloads dependencies while closing a cycle. Missing Node,
Playwright or Chromium produces a specific diagnostic, retaining the last valid
image. Linux may require Playwright's documented browser system dependencies
(`node scripts/media/node_modules/playwright/cli.js install-deps chromium`).

## Normal product contract

A root `index.html` automatically uses the bounded static profile. Other static
web roots may declare `.autonomous-company/media.json`:

```json
{
  "version": 1,
  "type": "static",
  "webRoot": "public",
  "entry": "/",
  "readySelector": "main",
  "icon": "public/icon.svg"
}
```

Optional `steps` is a maximum of six `{ "action": "click", "selector": "..." }`
or `{ "action": "fill", "selector": "...", "value": "..." }` records. These
perform ordinary UI interactions on real product content. There is no JavaScript
evaluation step or DOM injection. Use explicit built-in examples where helpful;
do not fabricate completion, check results or business data for a screenshot.
`timeoutSeconds` is an integer from 1 to 15 (default 10). Desktop 1440 × 1000 and
mobile 390 × 844 captures are fixed. Browser requests are limited to the owned
loopback origin; externally hosted fonts/assets and authenticated external
services are outside this contract. Screenshots prove appearance, not correctness.

For a CLI/nonvisual product use `{ "version": 1, "type": "none" }`. Missing
static entry or unsupported frameworks remain explicitly unsupported.

An explicit Node development-server profile is supported:

```json
{
  "version": 1,
  "type": "node",
  "webRoot": ".",
  "command": ["node", "preview.cjs", "{port}"],
  "healthPath": "/",
  "entry": "/",
  "readySelector": "main"
}
```

The argv is executed directly (no shell), from the product directory. The first
entry must be `node`, followed by an existing project-relative `.js`, `.cjs` or
`.mjs` file. Exactly one `{port}` placeholder is required. The server must bind to
`127.0.0.1` at that port, fail if it cannot acquire it, and return these headers
on both its health and entry responses:

```js
{
  "X-Autonomous-Company-Media": process.env.AUTONOMOUS_COMPANY_MEDIA_TOKEN,
  "X-Autonomous-Company-Version": process.env.AUTONOMOUS_COMPANY_MEDIA_VERSION
}
```

These random per-capture identity and content-version headers prevent a reused
port from producing a false success. A Vite project can explicitly configure
`server.headers` from these variables and pass its local Vite Node entrypoint
with `--host 127.0.0.1 --port {port} --strictPort`. The program never guesses npm
scripts, installs dependencies, reuses arbitrary URLs or kills a process by port.
The worker owns a short preview scope and recovers it after success, errors or
timeouts, including an exited worker leader. Windows uses a kernel Job Object;
POSIX tracks process birth identities (Linux also uses pidfds). Development
servers must keep their children within the managed process scope rather than
daemonizing or handing execution to an external service. The overall capture
deadline is 45 seconds plus bounded cleanup;
an independent worker watchdog also limits lifetime after owner failure.
Stopping the loop cancels an in-progress cycle-finalization capture. Closed model
and check results remain recorded, and stop cleanup never starts a new capture.

## Product icon

Use `icon.svg`, or set the profile's product-relative `icon` path. Existing
`favicon.svg`, `public/icon.svg` and `public/favicon.svg` are also considered.
The normal frontend workflow should author the input `icon.svg` and reference the
program-owned **output** `autonomous-company-icon.svg` for its visible product icon and
favicon, for example `<link rel="icon" href="autonomous-company-icon.svg"
type="image/svg+xml">`. During delivery/capture the collector writes the validated
or default bytes to that canonical file in the declared `webRoot`, matching the
Dashboard asset. For Node profiles, declare the actual public asset root (for
example `public` for Vite). The coding model must leave the canonical output to
the program. This narrowly scoped generated-icon write happens before version
hashing. For supported static `.html`/`.htm` entries with one explicit `<head>`,
the collector also checks the favicon reference. If no usable favicon exists,
it inserts one `<link rel="icon">` before `</head>`, marked
`data-autonomous-company-icon="v1"`. Its href is relative to the HTML entry:
`autonomous-company-icon.svg` at the Web root or `../autonomous-company-icon.svg` for a
one-level nested entry, preserving file previews and deployment subpaths. It preserves
all original bytes and business DOM; correct references are left unchanged.
Existing validated user SVG favicons are preserved and reported as not unified
when their bytes differ from the Dashboard icon. Raster favicons, which this SVG
validator cannot verify, are preserved with an unconfirmed reference. External or conditional choices,
`<base>` URLs, dynamic Node entries, unsupported encodings and implicit/malformed
heads are left untouched with explicit unconfirmed/unsupported diagnostics.
Title/script/style text never counts as an icon element. Self-closing/unclosed
text elements, business content before the head, premature head-ending tokens
and head template/noscript blocks fail closed without writing or claiming linkage.
Head scripts containing `<` in their text and nonstandard closing tokens such as
`</ script>` or `</ head>` are also unsupported; empty external-script elements
remain supported. The collector deliberately does not implement HTML5's complex
script parsing modes.
Modified owned references are not overwritten. No reference is inserted unless
the canonical file is available and validated. An existing conflicting
canonical file is preserved, with `publicationStatus: "conflict"`. Previously
program-owned output is only replaced while its bytes still match its ownership
record; a subsequent manual edit is preserved too. `publicationStatus` describes
file publication; `reference` separately describes the static entry's favicon
linkage. This is source evidence, not a guarantee about later JavaScript changes
or the browser's favicon selection. Capture/linkage failures remain independent
of functional checks and AI-cycle completion.

Accepted SVGs have a finite `viewBox`, at most 64 simple shape/group elements and
32 KiB. Scripts, event handlers, external resources, style sheets, entities,
animation, foreign objects and text are rejected. A valid existing product icon
is reused; otherwise a deterministic geometric default is stored with
`source: "default"` and the reason. This validates safe static structure, not
aesthetic quality. No dedicated image model is called.

## Artifacts and read APIs

`product_media.capture_product(root, project, cycle_id=None, trigger="cycle",
readonly=False, retry=False)` is a write/execute operation. It requires an
existing stable product identity, refuses `readonly=True`, and uses a kernel
lock. Concurrent capture returns `capture_busy` without starting another worker.
Because Windows byte locks and Linux file locks do not interoperate on shared
filesystems, a one-time atomic `writer.json` binding limits a managed media folder
to its original Windows/POSIX writer family (`nt`/`posix`). A capture from the other OS fails with
`writer_runtime_mismatch`; read-only display continues to work in either OS.
Use the original runtime for retries; copying an archive does not authorize a
different execution environment to take ownership of its media writes.

The explicit operator retry command is:

```sh
python3 scripts/core/runtime_artifacts.py --project projects/example media --retry
```

Run it through the product's normal runtime (WSL for a WSL-owned product). It does
not invoke an AI model. Repeated automatic triggers reuse the same product,
content and capture-steps version; failed versions require explicit retry or a
source/configuration change. A source change during capture cannot be published
as success. Captures stay outside product source; only the declared canonical
icon and the narrowly scoped static-head metadata insertion are written there.
Read-only archives cannot execute either write.

`media_projection(root, project, readonly=False)` is a pure read. Its `screenshot`
includes `state`, `reason`, `currentVersion`, `stale`, `attemptedAt` and
`latestSuccess`. States are `missing`, `capturing`, `interrupted`, `success`,
`failed`, `stale`, `unsupported` and `not_applicable`. `latestSuccess` contains
`version`, `cycleId`, `capturedAt`, `pagePath`, `attemptId` and two `variants`
(`viewport`, `width`, `height`, `sha256`, `name`, `href`). `icon` contains `source`
(`product` or `default`), `sha256`, `name`, `href`, `reason`, `recordedAt`,
`publicationStatus` (`published`, `existing_valid`, `conflict`, `failed`, `stale`,
`unavailable` or `not_applicable`) and, where relevant,
`publicationReason`/`publishedPath`. Pure reads verify previously published bytes
and expose subsequent edits or missing canonical files without repairing them.
`icon.reference` contains `state`, `reason`, `unified`, `managed` and, when known,
`href`, `entryPath` and `entrySha256`. Its states are `inserted`, `linked`,
`preserved`, `missing`, `not_applicable`, `unsupported`, `unconfirmed`, `conflict`
and `failed`. Only confirmed matching bytes have `unified: true`; preserved
different user icons have `false`; unsupported/unknown states remain `null`.
GET projections re-inspect the source and never insert or repair a reference.

`read_resource(root, stable_id, name)` returns `(bytes, mime)` or `None`. The HTTP
adapter serves `/api/product-media/<hex32 stable ID>/<sha256>.png|svg`. Only
registered, digest-validated current images and safe SVGs are readable. Raw paths,
traversal, symlinks, modified files and unregistered files are rejected. Serve SVG
as an image with `nosniff`; do not inject it into the document.

Generated captures and their metadata live in `logs/product-media/<stable ID>/`.
The declared canonical product icon and the bounded static-head metadata link
are the only changes written into product source.
`media.json` is
committed atomically after both image files; `attempt-<ID>.json` records each
attempt. Failure preserves the latest intact success and its original timestamp.
Reads compute source freshness but do not repair records or start captures.
All distinct delivery images and the five most recent ordinary captures are
retained; older ordinary images and replaced icons are pruned. Attempt/cycle
metadata is retained. Product version hashing is bounded to 2,048 supported source
files and 24 MiB, excluding dependency, hidden and generated check trees.
