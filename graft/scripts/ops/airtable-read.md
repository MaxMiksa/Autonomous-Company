# scripts/ops/airtable-read.py · [[airtable-linear-external-integrations]] [[runtime-environment-secrets]]

The only sanctioned way for a cycle to read an Airtable table, enforcing strict query scoping and compact output to keep context re-read costs low.

- Refusal · class · L68-L69 — Exception type that names a scoping mistake precisely so the caller can print the flag that fixes it.
- load_env · function · L72-L92 — Fills missing AIRTABLE_API_KEY/BASE_ID from logs/runtime.env without echoing the secret.
- load_keychain · function · L95-L111 — Last-resort secret retrieval from the macOS keychain for operators outside the container.
- build_params · function · L114-L173 — Turns CLI flags into Airtable query params, refusing any read that is unscoped or over the row/column ceilings.
- encode · function · L176-L183 — Flattens the params dict into a URL-encoded query string, expanding list values into repeated keys.
- to_body · function · L186-L198 — Converts the query params into the POST /listRecords JSON body form, remapping fields[] and sort keys.
- request · function · L201-L217 — Performs the HTTP GET/POST to Airtable and returns parsed JSON, redacting the token from any error output.
- fetch · function · L220-L239 — Pulls records across pages, switching to POST /listRecords when the URL would exceed the cap, and stops at the requested count.
- clip · function · L242-L248 — Truncates long string cell values with a marker so nobody mistakes a cut value for the whole.
- main · function · L251-L343 — Parses args, enforces scoping, fetches records, and prints compact rows plus a context-cost footer.
