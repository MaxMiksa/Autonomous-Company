---
name: Context7 Docs Wrapper
slug: context7-docs-wrapper
type: file
sources:
  - path: >-
      scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh
    hash: 79198378c25b2ff21cf5e4e2eda13f55c29ac806bd7f9d2bb0cba11a6268c447
sources_digest: d015b3a02ab7360603b113092f672eafcdd3a21270b3ab056880f098f44b12c1
links:
  - to: opportunity-analyst
    relation: part_of
    description: Skill script used by the opportunity director skill.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Bash CLI wrapping the Context7 API to fetch library documentation context for the autocompany opportunity director. Exposes check/search/docs subcommands, resolves an API key via CONTEXT7_API_KEY env var or macOS Keychain, and uses strict argument validation with set -euo pipefail.

## Related

- part of [[opportunity-analyst]] — Skill script used by the opportunity director skill.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
