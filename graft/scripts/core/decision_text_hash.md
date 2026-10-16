# scripts/core/decision_text_hash.py · [[content-hash-provenance]]

Canonical content hash for a KİK decision page, normalizing raw HTML into byte-identical text so both ends of the bridge compute the same hash regardless of client.

- normalize · function · L54-L60 — Normalizes raw page bytes into canonical text by dropping script/style elements and tags, unescaping entities, mapping NBSP, and collapsing whitespace so the hash is client-independent.
- digest · function · L63-L65 — Computes the truncated sha256 hex digest and character count of the normalized decision text.
- fetch · function · L68-L96 — Retrieves the page bytes using urllib with a browser User-Agent, falling back to curl when the TLS handshake is rejected.
- main · function · L99-L112 — CLI entry point that hashes a URL, saved HTML file, or already-extracted text and prints the sha256 prefix and char count.
