---
name: Turn-Economy & Bloat Monitoring
slug: turn-economy-bloat-monitoring
type: system
sources:
  - path: scripts/ops/bloat-trend.py
    hash: f74441749dee8335f3eb7b9fa4626fcde6b9903cf0006019a261e8c35115fe26
  - path: scripts/ops/context7-check.py
    hash: 4687b776e558caf660fad0d984e405c6a9498525648273569ac9a5feb544797e
sources_digest: 2e7d12351bfa4e3ef88218329017cea3608968ce27f861798a4563c6d1340d69
links:
  - to: auto-company-loop-orchestration
    relation: uses
    description: Reads turn-audit lines from auto-loop.log
  - to: telegram-notification-channel
    relation: uses
    description: Sends regression/target alerts via telegram-notify.sh
generator:
  version: 1
covers:
  - symbol: ingest
    kind: function
    at: 'scripts/ops/bloat-trend.py:L54-L97'
  - symbol: is_bloated
    kind: function
    at: 'scripts/ops/bloat-trend.py:L109-L110'
  - symbol: summarise
    kind: function
    at: 'scripts/ops/bloat-trend.py:L113-L126'
  - symbol: pct
    kind: function
    at: 'scripts/ops/bloat-trend.py:L117-L118'
  - symbol: notify
    kind: function
    at: 'scripts/ops/bloat-trend.py:L129-L142'
  - symbol: fmt
    kind: function
    at: 'scripts/ops/bloat-trend.py:L145-L155'
  - symbol: d
    kind: function
    at: 'scripts/ops/bloat-trend.py:L146-L151'
  - symbol: main
    kind: function
    at: 'scripts/ops/bloat-trend.py:L158-L237'
  - symbol: hits_target
    kind: function
    at: 'scripts/ops/bloat-trend.py:L185-L187'
  - symbol: externals
    kind: function
    at: 'scripts/ops/context7-check.py:L59-L75'
  - symbol: scan
    kind: function
    at: 'scripts/ops/context7-check.py:L78-L108'
  - symbol: walk_calls
    kind: function
    at: 'scripts/ops/context7-check.py:L111-L122'
  - symbol: verdict
    kind: function
    at: 'scripts/ops/context7-check.py:L125-L138'
  - symbol: main
    kind: function
    at: 'scripts/ops/context7-check.py:L141-L170'
---
<!-- context:generated:start -->
## Summary

Watchers that measure and police per-cycle turn economy: bloat-trend.py ingests audit lines from auto-loop.log into a durable NDJSON history and compares sliding windows, alerting only on regression (p90 turns worsening ≥20% and bloated share doubling), target met (two consecutive windows), or explicit --report — recomputing stored verdicts from raw numbers using current thresholds because thresholds changed on 2026-08-02. context7-check.py is a compliance checker detecting whether an agent wrote code importing an external library without first calling the Context7 MCP tool, deliberately avoiding prefiltering on exact JSON strings that caused silent false negatives.

## Related

- uses [[auto-company-loop-orchestration]] — Reads turn-audit lines from auto-loop.log
- uses [[telegram-notification-channel]] — Sends regression/target alerts via telegram-notify.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
