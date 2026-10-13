---
name: set -e shape lint
slug: set-e-shape-lint
type: concept
sources:
  - path: tests/test_seteshape_lint.py
    hash: c75dd121edbe7aed5432f718bdfff952149464b77f9ab22baced3682261ebc98
sources_digest: bb485dc41fe2695620287c9f61a662378b47a6f7a52a7d87a6d4b941bd639c6c
links:
  - to: auto-loop-core-engine
    relation: validates
    description: Lints auto-loop.sh and docker-entrypoint.sh for the fatal set -e pattern
generator:
  version: 1
covers:
  - symbol: _is_fatal_shape
    kind: function
    at: 'tests/test_seteshape_lint.py:L42-L43'
  - symbol: _executable_lines
    kind: function
    at: 'tests/test_seteshape_lint.py:L46-L52'
  - symbol: find_violations
    kind: function
    at: 'tests/test_seteshape_lint.py:L55-L84'
  - symbol: SetEShapeLint
    kind: class
    at: 'tests/test_seteshape_lint.py:L87-L99'
  - symbol: test_no_fatal_test_and_shapes
    kind: method
    at: 'tests/test_seteshape_lint.py:L88-L99'
---
<!-- context:generated:start -->
## Summary

A deliberately narrow lint (APP-240 root cause) that flags the fatal pattern of a `[ test ] && action` list used as a function's last command or immediately before a bare `return`, which propagates a false test's exit status 1 and kills an unguarded caller. It deliberately does not flag done/fi/esac terminators (set -e exempts the left operand of AND-OR lists) and skips lines ending in `|| true`/`|| :`, to avoid false-positives on the safe redirect-fed loop form used by docker-entrypoint.sh's runtime.env parser.

## Related

- validates [[auto-loop-core-engine]] — Lints auto-loop.sh and docker-entrypoint.sh for the fatal set -e pattern
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
