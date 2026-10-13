# scripts/ops/airtable-write.py · [[airtable-access-wrapper]] [[external-data-access-airtable-browser-ki-k]] [[secret-management-runtime-env-keychain]]

CLI tool that performs single-record Airtable writes with mandatory before/after read-back, dry-run-by-default, and data-loss guards so operator-side corrections never silently destroy or strand data.

- load_env · function · L46-L62 — Fills missing AIRTABLE_API_KEY and AIRTABLE_BASE_ID from logs/runtime.env without ever exposing the secret in argv or output.
- load_keychain · function · L65-L80 — Fetches the Airtable PAT from the macOS keychain as a last resort, passing only the service name in argv so the secret never appears in process listings.
- call · function · L83-L92 — Performs an authenticated Airtable HTTP request and surfaces API errors as a clean exit message without ever printing the bearer key.
- guard · function · L98-L133 — Decides from data alone whether a write must be refused, enforcing the clear, missing-field, and substantial-overwrite rules so a fix cannot silently destroy existing evidence.
- show · function · L136-L142 — Prints a labeled field/value listing for before/after/read-back comparison, truncating long values and marking empties.
- main · function · L145-L202 — Orchestrates the write flow: loads credentials, reads the target row, runs guards, and on --apply patches then verifies the read-back equals what was sent.
