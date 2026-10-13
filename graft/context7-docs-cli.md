---
name: Context7 Docs CLI
slug: context7-docs-cli
type: file
sources:
  - path: >-
      scripts/analyst/codex-skill/autocompany-opportunity-director/scripts/context7_docs.sh
    hash: 79198378c25b2ff21cf5e4e2eda13f55c29ac806bd7f9d2bb0cba11a6268c447
sources_digest: d015b3a02ab7360603b113092f672eafcdd3a21270b3ab056880f098f44b12c1
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Bash wrapper around the Context7 API to fetch library documentation context for the autocompany opportunity director. Three subcommands: check (auth/search connectivity), search (libraries by name/query), docs (context snippets for a library ID, json or txt output). Resolves API key via CONTEXT7_API_KEY env or macOS Keychain service autocompany-context7-key. Strict argument validation, set -euo pipefail, fallback plain-text when jq absent.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
