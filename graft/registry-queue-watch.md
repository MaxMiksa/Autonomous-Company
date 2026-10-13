---
name: registry queue watch
slug: registry-queue-watch
type: file
sources:
  - path: scripts/ops/registry-queue-watch.py
    hash: 0ef6723d089c54ee8272050eb2776ce81af9de986e8f6dc15b065b7bbd913497
  - path: tests/test_registry_queue_watch.sh
    hash: 0c823a0b115d8fb57d7a64e25cb89f725943078e58504a22aa5306a416ac6668
sources_digest: 878ae52108871773ccdef2f91facc355fd5f130052a7558e98c93f83cf21f6fd
links:
  - to: registry-archive
    relation: uses
    description: Both operate on the candidate registry markdown
generator:
  version: 1
covers:
  - symbol: api_key
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L48-L58'
  - symbol: fetch
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L61-L77'
  - symbol: main
    kind: function
    at: 'scripts/ops/registry-queue-watch.py:L80-L215'
---
<!-- context:generated:start -->
## Summary

scripts/ops/registry-queue-watch.py (APP-277) watches the registry queue, firing only above threshold and respecting cooldown, and never misattributes a bottleneck: an empty bridge queue with many attribution-Held firms is a company gap, not an operator gap. Distinguishes EKAP-only queue detection (a v1 blind spot), persists cooldown via .registry-queue-state.json, and clears state when the queue drains so the next backlog alerts immediately.

## Related

- uses [[registry-archive]] — Both operate on the candidate registry markdown
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
