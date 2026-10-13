---
name: Cost & Budget Accounting
slug: cost-budget-accounting
type: system
sources:
  - path: scripts/core/engine-usage-cost.py
    hash: ed2abe259894787b3b28b7e9e9597f1bdfb7bbaf8b3aa9fdf47db72e2473da5f
  - path: scripts/ops/budget-calibration-report.py
    hash: 4773ab252d5a928ff27a3bb15b9df63d086258a96e76d0d679ebeba49985be21
  - path: scripts/ops/cost-audit.py
    hash: 5364d89f8098cbb2fd8e51d0ba2c3c79a26df3dd6b99abb97cfa228af0cb8867
  - path: scripts/ops/operator-usage-report.sh
    hash: c469a1b0ab7be7c2c839b0ba0cf5a73d755ffd7f6e3d9891f924e61f1428eb4b
sources_digest: f7de3b93d43c5a84a70a15d9fa29f796e95e947dc89ea787fd94ad0225aa9864
links:
  - to: auto-company-loop-orchestration
    relation: produces
    description: The loop's spend-total.log and auto-loop.log feed these auditors
  - to: consensus-memory-state-files
    relation: produces
    description: cost-audit.py writes memories/cost-audit.md
generator:
  version: 1
covers:
  - symbol: _n
    kind: function
    at: 'scripts/core/engine-usage-cost.py:L75-L78'
  - symbol: cost_for
    kind: function
    at: 'scripts/core/engine-usage-cost.py:L81-L123'
  - symbol: main
    kind: function
    at: 'scripts/core/engine-usage-cost.py:L126-L204'
  - symbol: split_by_cutover
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L72-L76'
  - symbol: pct
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L79-L84'
  - symbol: load_claude
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L87-L102'
  - symbol: load_codex
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L105-L138'
  - symbol: sliding
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L141-L157'
  - symbol: daily_buckets
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L160-L166'
  - symbol: stats_line
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L169-L173'
  - symbol: main
    kind: function
    at: 'scripts/ops/budget-calibration-report.py:L176-L289'
  - symbol: utc_day
    kind: function
    at: 'scripts/ops/cost-audit.py:L42-L43'
  - symbol: read_ledger
    kind: function
    at: 'scripts/ops/cost-audit.py:L46-L67'
  - symbol: read_loop_log
    kind: function
    at: 'scripts/ops/cost-audit.py:L70-L111'
  - symbol: read_jcode_log
    kind: function
    at: 'scripts/ops/cost-audit.py:L114-L131'
  - symbol: read_tool_inventory
    kind: function
    at: 'scripts/ops/cost-audit.py:L134-L141'
  - symbol: read_disabled_tools
    kind: function
    at: 'scripts/ops/cost-audit.py:L144-L171'
  - symbol: fmt_money
    kind: function
    at: 'scripts/ops/cost-audit.py:L174-L175'
  - symbol: build_report
    kind: function
    at: 'scripts/ops/cost-audit.py:L178-L339'
  - symbol: main
    kind: function
    at: 'scripts/ops/cost-audit.py:L342-L360'
---
<!-- context:generated:start -->
## Summary

The cost-tracking layer bridging token usage into the APP-263 budget ledger: engine-usage-cost.py converts token usage to notional USD using Anthropic list prices (summing all tokens events since done.usage undercounts multi-tool cycles, conservative 5x fallback for unknown models, STRICT=1 hard-fail), cost-audit.py is a deterministic daily auditor writing memories/cost-audit.md from on-disk logs only (never model estimates), budget-calibration-report.py generates APP-263 spend percentiles and gate-block counts with a CUTOVER_EPOCH splitting pre/post 5-hour-pause-gate policies, and operator-usage-report.sh pushes the operator's ccusage data into the container for calibration.

## Related

- produces [[auto-company-loop-orchestration]] — The loop's spend-total.log and auto-loop.log feed these auditors
- produces [[consensus-memory-state-files]] — cost-audit.py writes memories/cost-audit.md
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
