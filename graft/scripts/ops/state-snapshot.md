# scripts/ops/state-snapshot.py · [[state-snapshot-delta-probing]]

One-call cycle state snapshot that collapses the per-cycle probe fan-out into a single turn, printing local state hashes plus a DELTA line against the previous snapshot so an unchanged world can be dismissed in one glance.

- file_sha16 · function · L54-L61 — Computes a short sha256 fingerprint of a file for change detection, returning ABSENT for missing files and None for unreadable ones.
- directive_state · function · L64-L72 — Reads the human directive file and returns its Status section plus a sha16 fingerprint used purely for change detection.
- opreq_open · function · L75-L87 — Scans the operator-requests ledger and returns the ids of blocks whose Status is OPEN, so the cycle knows which requests still need work.
- wowcar_sources · function · L90-L104 — Builds a sha16 over the sorted per-file sha256 set of Wowcar source documents so a new or changed source file fires a DELTA.
- main · function · L107-L166 — Gathers all local state fields, prints them, and computes a DELTA against the persisted previous snapshot while excluding errored fields from comparison.
