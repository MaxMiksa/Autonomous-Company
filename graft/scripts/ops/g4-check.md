# scripts/ops/g4-check.py · [[g4-identity-attribution-verdict]]

CLI that mechanically rules on G4 identity attribution from live evidence (first-party contact plus a registered-identity anchor), so the closing decision follows evidence rather than a self-declared PASS.

- load_key · function · L71-L89 — Loads the Airtable API key from env, runtime.env, or macOS Keychain so the checker can authenticate.
- norm · function · L92-L100 — Normalizes Turkish address text into comparable tokens, folding dotted/dotless I variants and abbreviating street words so register and website spellings match.
- address_anchor · function · L103-L132 — Decides whether a page carries the registered address by requiring a strong combination of door numbers and distinctive name tokens, so a bare administrative tail can never pass.
- registry_id_anchor · function · L135-L164 — Checks whether the site prints a registry number (MERSİS, vergi no, or sicil) from the row, with digit-length-dependent context demands to avoid false matches.
- field · function · L167-L169 — Extracts a single label:value field from a pipe-separated row text.
- domains_in · function · L172-L180 — Collects candidate firm domains from text while excluding authority sources and the tool's own infrastructure.
- air_get · function · L183-L187 — Fetches one Airtable record's fields by id.
- air_list · function · L190-L195 — Lists Airtable records matching a filter formula.
- site_evidence · function · L198-L217 — Reuses the render-first examiner to get the site verdict and gathers page text from the domain and common contact pages for anchoring.
- judge · function · L220-L287 — Combines first-party contact, registered-address anchor, registry-id anchor, and profile-bridge evidence into a PASS/HOLD verdict, treating a claimed PASS as an assertion to be tested.
- main · function · L290-L337 — Orchestrates the CLI: loads the key, gathers rows, runs the judge on each, flags claimed-but-unverified PASSes loudly, and reports the pass count.
