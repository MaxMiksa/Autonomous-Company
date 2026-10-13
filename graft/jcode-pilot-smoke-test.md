---
name: jcode Pilot Smoke Test
slug: jcode-pilot-smoke-test
type: file
sources:
  - path: scripts/analyst/jcode-pilot-smoke.sh
    hash: 354473b12623cdd65b47b0245f7d2fe85e03182998cc3d114f5dd419ba944d99
sources_digest: 580997342635860ff744d27a36e889c902bd03a27837c94edb20c5bb745f01b5
links:
  - to: opportunity-analyst-jcode
    relation: validates
    description: Acceptance gate before the jcode analyst runs in production.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Acceptance smoke test for the jcode pilot container (autocompany-jcode:pilot) verifying five critical checks per RUNBOOK §0.4 while touching nothing persistent. Checks: GLIBC sanity, jcode binary runnability, Claude auth via CLAUDE_CODE_OAUTH_TOKEN wrapped in JSON blob with 300-day expiry, real model round-trip against claude-haiku-4-5-20251001 expecting 'OK', daemon-leak check via pgrep. Notable gotcha: as of jcode v0.64.2 the tool does NOT read the project's .mcp.json, so the script only verifies the file parses and registers servers — actual Airtable/Linear/BrowserOS connections deferred to second-stage checks from the real host. Uses set -uo pipefail (deliberately omitting -e), 180-second timeout on model call.

## Related

- validates [[opportunity-analyst-jcode]] — Acceptance gate before the jcode analyst runs in production.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
