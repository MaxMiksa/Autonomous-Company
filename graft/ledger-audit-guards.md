---
name: ledger & audit guards
slug: ledger-audit-guards
type: system
sources:
  - path: scripts/ops/ledger-guard.py
    hash: 5b3098424eada1d1f669995baf5e1dd76ea4fb724c0c524ddc9986ce361128d7
  - path: scripts/ops/tool-usage-audit.py
    hash: 73a75d68bab3e0b42e31ad3d268b44a8c7ac168b91c6a8d1b2f1b3cd4cdba975
  - path: scripts/ops/turn-audit.py
    hash: 11d7f3bda3ad3eafbc2874669f8bb2169288e01cba152cc213fd28d51f8cf77f
  - path: scripts/ops/turn-bloat-brake.py
    hash: c4d72b732830311e89db486abb41c8a13a5760ffa043354c953b99a155ff96fb
  - path: tests/test_ledger_guard.py
    hash: d0118c31c5f02cb01c7ad332056d6ec8c8951338d217999eda93e15dce90a354
  - path: tests/test_tool_usage_audit.sh
    hash: 4bdf9378fc2af04ed89fc9559aa1fcc8520846c6847f13302f613ec896bfde6d
  - path: tests/test_turn_audit.sh
    hash: ce3eb2af3fea266a763a0ca266f3c658f8498b604570c229141654d685f6c9e8
  - path: tests/test_turn_bloat_brake.py
    hash: 9599b12fa9480d0058872f2facb8d329c5deac8177df794c41982d955d887a74
sources_digest: 05f852c5ac39e46802f068d443ba8ced8904e8fd0ab42b04c8f194001a28e3c5
links:
  - to: auto-loop-core-engine
    relation: validates
    description: Audits the NDJSON cycle logs and ledger produced by the loop.
generator:
  version: 1
covers:
  - symbol: _env_int
    kind: function
    at: 'scripts/ops/ledger-guard.py:L43-L48'
  - symbol: _env_float
    kind: function
    at: 'scripts/ops/ledger-guard.py:L51-L55'
  - symbol: _app
    kind: function
    at: 'scripts/ops/ledger-guard.py:L58-L59'
  - symbol: _find_ledger
    kind: function
    at: 'scripts/ops/ledger-guard.py:L62-L69'
  - symbol: _metrics
    kind: function
    at: 'scripts/ops/ledger-guard.py:L72-L84'
  - symbol: _backup
    kind: function
    at: 'scripts/ops/ledger-guard.py:L87-L101'
  - symbol: _load_state
    kind: function
    at: 'scripts/ops/ledger-guard.py:L104-L108'
  - symbol: _save_state
    kind: function
    at: 'scripts/ops/ledger-guard.py:L111-L118'
  - symbol: _rebase_after_prune
    kind: function
    at: 'scripts/ops/ledger-guard.py:L125-L142'
  - symbol: _check
    kind: function
    at: 'scripts/ops/ledger-guard.py:L145-L170'
  - symbol: main
    kind: function
    at: 'scripts/ops/ledger-guard.py:L173-L240'
  - symbol: calls_from_ndjson
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L43-L65'
  - symbol: categorize
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L68-L121'
  - symbol: main
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L124-L251'
  - symbol: dump
    kind: function
    at: 'scripts/ops/tool-usage-audit.py:L177-L190'
  - symbol: ts_of
    kind: function
    at: 'scripts/ops/turn-audit.py:L74-L78'
  - symbol: scan
    kind: function
    at: 'scripts/ops/turn-audit.py:L81-L112'
  - symbol: floor_usd
    kind: function
    at: 'scripts/ops/turn-audit.py:L115-L121'
  - symbol: summary_line
    kind: function
    at: 'scripts/ops/turn-audit.py:L124-L142'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-audit.py:L145-L158'
  - symbol: _app
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L25-L26'
  - symbol: _streak_len
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L29-L34'
  - symbol: _load
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L37-L41'
  - symbol: _save
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L44-L51'
  - symbol: main
    kind: function
    at: 'scripts/ops/turn-bloat-brake.py:L63-L104'
  - symbol: newapp
    kind: function
    at: 'tests/test_ledger_guard.py:L15-L20'
  - symbol: ledger
    kind: function
    at: 'tests/test_ledger_guard.py:L23-L24'
  - symbol: run
    kind: function
    at: 'tests/test_ledger_guard.py:L27-L33'
  - symbol: body
    kind: function
    at: 'tests/test_ledger_guard.py:L36-L42'
  - symbol: check
    kind: function
    at: 'tests/test_ledger_guard.py:L45-L48'
  - symbol: newapp
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L15-L18'
  - symbol: rec
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L21-L27'
  - symbol: fb
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L30-L36'
  - symbol: consecutive
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L39-L40'
  - symbol: check
    kind: function
    at: 'tests/test_turn_bloat_brake.py:L43-L46'
---
<!-- context:generated:start -->
## Summary

Monitoring and integrity scripts: ledger-guard.py watches a ledger file for unexpected section/row/size changes with incident-note exemption and backup rotation; tool-usage-audit.py categorizes jcode NDJSON tool usage (script+MCP combined counts, per-MCP-tool-name only for MCP tools), is idempotent, backfills new cycle files, re-audits rewritten files (cycle counter resets on container restart), and counts browse-extract.py as browser usage; turn-audit.py implements turn-economy policy with verdict thresholds (CHATTY/BLOATED/ok) and boundary pins; turn-bloat-brake.py tracks consecutive BLOATED verdicts and fires an alarm after a streak threshold.

## Related

- validates [[auto-loop-core-engine]] — Audits the NDJSON cycle logs and ledger produced by the loop.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
