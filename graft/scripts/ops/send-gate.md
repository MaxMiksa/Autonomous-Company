# scripts/ops/send-gate.py · [[send-gate]]

Fail-closed gate that decides from live evidence whether a firm may be emailed, enforcing caps, no-duplicate, opt-out, and live G4 verification with the operator out of the loop.

- phase_of · function · L66-L91 — Determines which elimination stage the authority's own operative sentence describes, refusing (UNKNOWN) when it cannot be read so a wrong claim is never made to a firm.
- body_claims · function · L94-L101 — Reads which stage the message body asserts by matching the approved template's own wording.
- load_key · function · L104-L122 — Loads the Airtable API key from environment, runtime.env, or macOS keychain so gate checks can authenticate.
- air · function · L125-L135 — Performs an authenticated Airtable API request, quoting each path component so table names with spaces do not produce malformed URLs.
- sent_rows · function · L138-L148 — Returns every Outreach row that has actually been emailed, excluding TEST rows by status rather than name.
- logged_sends · function · L154-L177 — Derives total and today's send counts from a row's Email log Sent: entries, failing closed to a non-zero fallback so a real send never disappears from the cap.
- counts · function · L180-L198 — Aggregates distinct-firm exposures and log-derived message sends for today and total, the two counters the caps bind on.
- opted_out · function · L201-L215 — Detects whether a firm has opted out by scanning status/notes/log fields for the provider's own suppression wording, including the literal 'opted out' phrase.
- body_leak_scan · function · L236-L244 — Refuses a send whose body contains internal-only vocabulary, returning the exact marker hit so a refusal can be acted on rather than worked around.
- g4_live · function · L247-L309 — Re-derives G4 attribution live from the registry bridge, requiring an exact firm-name match and falling back to the Outreach row's own domain only when the bridge names none.
- decide · function · L312-L544 — Decides ALLOW or REFUSE for a record by checking caps, duplicate/opt-out, follow-up authorization, and live G4, refusing on any check that cannot be completed.
- main · function · L547-L583 — CLI entry point that runs the gate for a record or reports caps and current eligibility.
