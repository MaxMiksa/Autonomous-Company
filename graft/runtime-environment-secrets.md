---
name: Runtime environment & secrets
slug: runtime-environment-secrets
type: concept
sources:
  - path: scripts/core/directive_writer.py
    hash: 2b00db428f705544c6b980dd3b76f3e35e0dc76ca44eb82a2d023c7d1b9bb45a
  - path: scripts/ops/airtable-read.py
    hash: 148f66145510c90e03256b7b37853122bcd892d51cba67f095ce700a0895e3e2
  - path: scripts/ops/airtable-write.py
    hash: 888d408c392193511145e11dfbe73841a6d7e3e743e396ab8c8fee8b9507ab7c
  - path: scripts/ops/docker-prune-safe.sh
    hash: 7f22912e40c9235114d147f0fb3949880a970ed7104ffcee964c37b187a1cb1d
  - path: scripts/ops/linear-track.py
    hash: 5a0cc4bf3713dd3351302a4e9ed446432c92217afdbefd6fa9ee87a9ccd4f730
  - path: scripts/ops/operator-action-router.py
    hash: 25fd8206f44d0baa7b87a910d0d1846fe5ef1b155289d1a769994aff6817587e
  - path: scripts/ops/operator-usage-report.sh
    hash: c469a1b0ab7be7c2c839b0ba0cf5a73d755ffd7f6e3d9891f924e61f1428eb4b
sources_digest: 885eeba506f81dd1990ebe62508e8c40bfff0882b3bc78e9078d4be08ce1e47e
links: []
generator:
  version: 1
covers:
  - symbol: undefined_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L104-L113'
  - symbol: now
    kind: function
    at: 'scripts/core/directive_writer.py:L116-L117'
  - symbol: sha
    kind: function
    at: 'scripts/core/directive_writer.py:L120-L121'
  - symbol: read_live
    kind: function
    at: 'scripts/core/directive_writer.py:L124-L130'
  - symbol: body_of
    kind: function
    at: 'scripts/core/directive_writer.py:L133-L140'
  - symbol: audit
    kind: function
    at: 'scripts/core/directive_writer.py:L143-L149'
  - symbol: _telegram_env
    kind: function
    at: 'scripts/core/directive_writer.py:L152-L175'
  - symbol: notify
    kind: function
    at: 'scripts/core/directive_writer.py:L178-L188'
  - symbol: _why_pending
    kind: function
    at: 'scripts/core/directive_writer.py:L191-L219'
  - symbol: backup
    kind: function
    at: 'scripts/core/directive_writer.py:L222-L236'
  - symbol: normalize_ownership
    kind: function
    at: 'scripts/core/directive_writer.py:L239-L285'
  - symbol: atomic_write
    kind: function
    at: 'scripts/core/directive_writer.py:L288-L300'
  - symbol: verify_written
    kind: function
    at: 'scripts/core/directive_writer.py:L303-L307'
  - symbol: Refused
    kind: class
    at: 'scripts/core/directive_writer.py:L310-L311'
  - symbol: live_body
    kind: function
    at: 'scripts/core/directive_writer.py:L316-L319'
  - symbol: split_body
    kind: function
    at: 'scripts/core/directive_writer.py:L322-L345'
  - symbol: section_sizes
    kind: function
    at: 'scripts/core/directive_writer.py:L348-L352'
  - symbol: size_brake
    kind: function
    at: 'scripts/core/directive_writer.py:L355-L371'
  - symbol: _pending_gate
    kind: function
    at: 'scripts/core/directive_writer.py:L374-L390'
  - symbol: _refuse_section_refs
    kind: function
    at: 'scripts/core/directive_writer.py:L393-L401'
  - symbol: with_lock
    kind: function
    at: 'scripts/core/directive_writer.py:L404-L413'
  - symbol: wrapper
    kind: function
    at: 'scripts/core/directive_writer.py:L405-L412'
  - symbol: cmd_write
    kind: function
    at: 'scripts/core/directive_writer.py:L426-L480'
  - symbol: cmd_append
    kind: function
    at: 'scripts/core/directive_writer.py:L484-L512'
  - symbol: cmd_archive
    kind: function
    at: 'scripts/core/directive_writer.py:L516-L580'
  - symbol: cmd_status
    kind: function
    at: 'scripts/core/directive_writer.py:L584-L618'
  - symbol: cmd_restore
    kind: function
    at: 'scripts/core/directive_writer.py:L622-L658'
  - symbol: cmd_show
    kind: function
    at: 'scripts/core/directive_writer.py:L661-L672'
  - symbol: main
    kind: function
    at: 'scripts/core/directive_writer.py:L675-L733'
  - symbol: _refuse_forbidden
    kind: function
    at: 'scripts/core/directive_writer.py:L714-L720'
  - symbol: fn
    kind: function
    at: 'scripts/core/directive_writer.py:L715-L719'
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
  - symbol: _now
    kind: function
    at: 'scripts/ops/operator-action-router.py:L78-L79'
  - symbol: read_hold
    kind: function
    at: 'scripts/ops/operator-action-router.py:L82-L102'
  - symbol: read_opreqs
    kind: function
    at: 'scripts/ops/operator-action-router.py:L105-L118'
  - symbol: read_directive
    kind: function
    at: 'scripts/ops/operator-action-router.py:L121-L134'
  - symbol: collect_items
    kind: function
    at: 'scripts/ops/operator-action-router.py:L137-L174'
  - symbol: render
    kind: function
    at: 'scripts/ops/operator-action-router.py:L177-L183'
  - symbol: set_hash
    kind: function
    at: 'scripts/ops/operator-action-router.py:L186-L189'
  - symbol: should_notify
    kind: function
    at: 'scripts/ops/operator-action-router.py:L192-L207'
  - symbol: load_state
    kind: function
    at: 'scripts/ops/operator-action-router.py:L210-L214'
  - symbol: write_state
    kind: function
    at: 'scripts/ops/operator-action-router.py:L217-L225'
  - symbol: clear_state
    kind: function
    at: 'scripts/ops/operator-action-router.py:L228-L232'
  - symbol: notify
    kind: function
    at: 'scripts/ops/operator-action-router.py:L235-L251'
  - symbol: main
    kind: function
    at: 'scripts/ops/operator-action-router.py:L254-L296'
---
<!-- context:generated:start -->
## Summary

The convention that credentials and runtime config live in logs/runtime.env (or macOS Keychain for GUI-launched processes), loaded by scripts rather than passed as argv to avoid ps leaks. Many scripts deliberately avoid dot-sourcing the env file because values contain '|', and docker exec paths read it from /app/logs/runtime.env. Secrets are never printed or passed as arguments.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
