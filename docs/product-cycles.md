# Continuous product cycles

A product's displayed work number persists across process restarts, model changes
and log rotation. An execution cycle is one coordinator attempt, not a business
stage or a completion threshold. Existing objectives, budgets, governance and
stop controls still apply. This feature does not impose a local-MVP stop or a
fixed number of cycles before delivery.

The program owns `.autonomous-company/product-state.json`: stable identities, counters,
cycle IDs and pending/terminal attempts are committed together. Product source
markers detect replaced directories; their names and paths are not identity.
The language-period `AUTONOMOUS_COMPANY_PRODUCT_ID` remains separate. Cycle processes
receive the new `AUTONOMOUS_COMPANY_STABLE_PRODUCT_ID` and
`AUTONOMOUS_COMPANY_PRODUCT_CYCLE_NUMBER` context.

New records count from 1. Legacy usage records retain their original IDs and
run-local numbers under “Legacy runs”; their history is never silently rewritten
as a complete lifetime sequence. The adoption point is the start of continuous
counting for an existing product. Rotation cannot reset the durable counter.

Before a product is selected, exploration has a separate identity and number.
`make project-new` explicitly links that exploration to the created product;
later automatic runs continue it without editing human selection. Early
exploration remains labeled separately. A second competing creation in the same
exploration is rejected rather than silently changing the continuation.

Startup preflight failures do not allocate a work cycle. An allocated attempt
is never reused: a reservation without dispatch stays “not started”; dispatch
without execution evidence stays “launch unconfirmed”. Retained execution
evidence permits an interrupted classification. Recovery does not
replay a possibly executed provider call. Ordinary restart recovery is automatic;
existing governance pauses still require the existing explicit resume workflow.

For a source directory deliberately moved within a runtime, preserve its marker
and use the identity tool's explicit `--project projects/<slug> relocate --id <id>`
command (`--root` identifies the runtime). Update human selection separately if
one is set. Missing/replaced sources do not inherit the old identity by filename.

If a writer is killed inside the short state transaction, the program retains a
lock and transaction intent. After confirming **all writers are stopped**, use:

```sh
python3 scripts/core/product_identity.py --root /path/to/runtime recover-lock --confirm STOPPED
```

This replays a saved transaction intent before further writes. It is not a way
to bypass an active writer. Keep the state directory with its runtime when
backing up or restoring; deleting it discards the counting authority. Readers do
not create identities or recover locks. Multi-product management and scheduling
are separate work and are not added by this change.
