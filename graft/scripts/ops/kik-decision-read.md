# scripts/ops/kik-decision-read.py · [[external-data-access-airtable-browser-ki-k]] [[ki-k-decision-content-hash-canon]] [[ki-k-decision-reader]]

One-call reader that fetches a KİK decision and returns only the fields a G1/outcome call needs, bounding bytes entering the context.

- _hasher · function · L45-L51 — Loads the single canonical decision_text_hash module so the content hash is comparable with what the bridge recorded.
- fetch · function · L54-L67 — Fetches the decision page with curl and a browser UA, retrying empty bodies so a transient miss never costs the caller a turn.
- text_of · function · L70-L73 — Strips scripts, styles, and tags from raw HTML and collapses whitespace into plain text.
- first · function · L76-L78 — Returns the first capture group of a regex search, or None.
- field · function · L81-L89 — Extracts a label's value from text, cutting it at the next all-caps label so adjacent blocks don't leak in.
- read · function · L92-L131 — Builds the digest of a decision: exact-shape identifiers, complainant, operative verdict, and exclusion sentences with legislation quotes dropped.
- main · function · L134-L159 — CLI entry that reads each id and prints either full JSON or a human digest.
