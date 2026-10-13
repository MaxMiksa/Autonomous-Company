---
name: spending controls & ledger
slug: spending-controls-ledger
type: concept
sources:
  - path: tests/test_discretionary_budget.sh
    hash: 32b2f12385f1bf8cc0984fc89d1181074406a1726028d2705d2224759cf6de7e
sources_digest: 62ecf9826e8ee0e90ec861065f7d213575d9326c4b34ca2b9c4d42e24b0475af
links:
  - to: auto-loop-core-engine
    relation: part_of
    description: Wiring lives in auto-loop.sh
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

Two spending-control mechanisms in auto-loop.sh: idle detection based on snapshot text 'DELTA: none' (fails open), and a discretionary daily cap that injects a warning line into the prompt once the day's spend reaches a threshold (default $30, compared with >= so an exact match triggers). The ledger is discretionary-spend.ndjson, summed for today's UTC date, skipping malformed lines and returning 0.00 on a missing file. The cap line is injected at exactly two sites (one per prompt branch).

## Related

- part of [[auto-loop-core-engine]] — Wiring lives in auto-loop.sh
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
