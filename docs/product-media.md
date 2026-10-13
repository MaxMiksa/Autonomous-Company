# Automatic product screenshots and icons

Normal delivery registration and cycle close capture supported product UIs
without requiring the coding model to open a preview or call a screenshot tool.
The existing single-product journal shows actual desktop/mobile images, their
source version/time and explicit missing, failed or stale states. Captures are
appearance records, not business completion or functional verification.

For a static product, a root `index.html` is enough. Other web roots and the
explicit Node development-server contract use `.autonomous-company/media.json`.
Nonvisual products can declare `{"version":1,"type":"none"}`. Unknown frameworks,
external/login-dependent resources and arbitrary startup commands are not guessed.

The optional screenshot runtime uses Node 20+ and the same pinned Playwright
Chromium dependency as the existing browser checks. Install it in the product's
runtime OS; capture never installs tools automatically. Missing tools preserve
the last valid image and produce a diagnostic. A manual retry does not invoke AI.

During capture/delivery, supported static HTML entries also receive a marked
favicon metadata link when one is missing and the validated canonical icon is
available. Correct references and existing usable user favicons are preserved;
different user icons, conflicts and dynamic/unknown references are reported
explicitly. This does not rewrite business content or add visible interface
elements. Read-only pages only inspect linkage and never repair it.

See [the media runtime contract](../scripts/media/README.md) for installation,
profile examples, safe SVG rules, cleanup and retention, explicit retry commands,
and the pure-read projection/resource APIs. Generated captures stay under
`logs/product-media/<stable product ID>/`; read-only archives cannot start capture.
