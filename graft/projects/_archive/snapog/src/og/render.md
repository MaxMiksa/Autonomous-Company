# projects/_archive/snapog/src/og/render.ts · [[snapog-og-rendering]]

Module that renders OG images and builds deterministic cache keys for them.

- generateOGImage · function · L11-L23 — Renders an OG image as a 1200x630 ImageResponse from the built element.
- buildCacheKey · function · L26-L37 — Produces a stable SHA-256 hash of sorted OG params so identical requests share a cache key.
