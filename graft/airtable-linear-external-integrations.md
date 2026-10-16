---
name: Airtable & Linear external integrations
slug: airtable-linear-external-integrations
type: system
sources:
  - path: scripts/ops/airtable-read.py
    hash: 148f66145510c90e03256b7b37853122bcd892d51cba67f095ce700a0895e3e2
  - path: scripts/ops/airtable-write.py
    hash: 888d408c392193511145e11dfbe73841a6d7e3e743e396ab8c8fee8b9507ab7c
  - path: scripts/ops/linear-track.py
    hash: 5a0cc4bf3713dd3351302a4e9ed446432c92217afdbefd6fa9ee87a9ccd4f730
sources_digest: d78127a23e85fa7a83bd4d475249bcc21bbefb30a628ebd8dada550aa0c7198b
links: []
generator:
  version: 1
covers:
  - symbol: Refusal
    kind: class
    at: 'scripts/ops/airtable-read.py:L68-L69'
  - symbol: load_env
    kind: function
    at: 'scripts/ops/airtable-read.py:L72-L92'
  - symbol: load_keychain
    kind: function
    at: 'scripts/ops/airtable-read.py:L95-L111'
  - symbol: build_params
    kind: function
    at: 'scripts/ops/airtable-read.py:L114-L173'
  - symbol: encode
    kind: function
    at: 'scripts/ops/airtable-read.py:L176-L183'
  - symbol: to_body
    kind: function
    at: 'scripts/ops/airtable-read.py:L186-L198'
  - symbol: request
    kind: function
    at: 'scripts/ops/airtable-read.py:L201-L217'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/airtable-read.py:L220-L239'
  - symbol: clip
    kind: function
    at: 'scripts/ops/airtable-read.py:L242-L248'
  - symbol: main
    kind: function
    at: 'scripts/ops/airtable-read.py:L251-L343'
  - symbol: load_env
    kind: function
    at: 'scripts/ops/airtable-write.py:L46-L62'
  - symbol: load_keychain
    kind: function
    at: 'scripts/ops/airtable-write.py:L65-L80'
  - symbol: call
    kind: function
    at: 'scripts/ops/airtable-write.py:L83-L92'
  - symbol: guard
    kind: function
    at: 'scripts/ops/airtable-write.py:L98-L133'
  - symbol: show
    kind: function
    at: 'scripts/ops/airtable-write.py:L136-L142'
  - symbol: main
    kind: function
    at: 'scripts/ops/airtable-write.py:L145-L202'
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

Scoped, auditable access to Airtable and Linear. Airtable reads refuse unscoped whole-table pulls (which cost $2.41/cycle in context re-reads) and writes are single-record, read-verify-write-verify with dry-run default and guards against clearing/replacing substantial data. Linear enforces a workstream discipline of appending checklist items to long-lived track issues rather than opening new issues, with hardcoded justifications for real issue creation.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
