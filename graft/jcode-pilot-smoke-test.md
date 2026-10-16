---
name: jcode Pilot Smoke Test
slug: jcode-pilot-smoke-test
type: concept
sources:
  - path: scripts/analyst/jcode-pilot-smoke.sh
    hash: 354473b12623cdd65b47b0245f7d2fe85e03182998cc3d114f5dd419ba944d99
sources_digest: 580997342635860ff744d27a36e889c902bd03a27837c94edb20c5bb745f01b5
links:
  - to: autonomous-loop-orchestrator
    relation: validates
    description: Validates the jcode harness used by auto-loop.sh.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Acceptance smoke test (jcode-pilot-smoke.sh) for the jcode pilot container verifying five checks per RUNBOOK §0.4: GLIBC sanity, jcode binary runnability, Claude auth (wrapping CLAUDE_CODE_OAUTH_TOKEN into a JSON blob with 300-day expiry), a real model round-trip against claude-haiku-4-5-20251001, and a daemon-leak check. Documents a critical gotcha: as of jcode v0.64.2 the tool does NOT read the project's .mcp.json, so the script only verifies the file parses and registers servers—actual Airtable/Linear/BrowserOS connections are deferred to second-stage checks from the real host.

## Related

- validates [[autonomous-loop-orchestrator]] — Validates the jcode harness used by auto-loop.sh.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
