---
name: Linear Workstream Tracking
slug: linear-workstream-tracking
type: file
sources:
  - path: scripts/ops/linear-track.py
    hash: 5a0cc4bf3713dd3351302a4e9ed446432c92217afdbefd6fa9ee87a9ccd4f730
sources_digest: ab4334d9d2bf19461212de4e4796a9e06c905727151e75e3aa148fac2d49e754
links:
  - to: secret-management-runtime-env-keychain
    relation: uses
    description: Resolves LINEAR_API_KEY from env or macOS Keychain
generator:
  version: 1
covers:
  - symbol: key
    kind: function
    at: 'scripts/ops/linear-track.py:L65-L79'
  - symbol: gql
    kind: function
    at: 'scripts/ops/linear-track.py:L82-L88'
  - symbol: get_issue
    kind: function
    at: 'scripts/ops/linear-track.py:L91-L97'
  - symbol: set_description
    kind: function
    at: 'scripts/ops/linear-track.py:L100-L102'
  - symbol: cmd_list
    kind: function
    at: 'scripts/ops/linear-track.py:L105-L120'
  - symbol: cmd_add
    kind: function
    at: 'scripts/ops/linear-track.py:L123-L131'
  - symbol: cmd_done
    kind: function
    at: 'scripts/ops/linear-track.py:L134-L145'
  - symbol: cmd_comment
    kind: function
    at: 'scripts/ops/linear-track.py:L148-L152'
  - symbol: cmd_new
    kind: function
    at: 'scripts/ops/linear-track.py:L155-L170'
  - symbol: main
    kind: function
    at: 'scripts/ops/linear-track.py:L173-L196'
---
<!-- context:generated:start -->
## Summary

linear-track.py enforces a workstream discipline: instead of opening a new issue for every finding, it appends checklist items to one long-lived track issue per workstream (APP-269, APP-276, APP-277, APP-246, APP-221). It talks to the Linear GraphQL API, with subcommands to list tracks, append checklist lines, tick matching items (refusing ambiguous matches), post evidence comments, and create real issues only if --why matches one of three hardcoded justifications. Handles Linear's normalization of ticked boxes to uppercase - [X].

## Related

- uses [[secret-management-runtime-env-keychain]] — Resolves LINEAR_API_KEY from env or macOS Keychain
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
