---
name: set -e shape lint
slug: set-e-shape-lint
type: concept
sources:
  - path: docker-entrypoint.sh
    hash: fbc2010d8d1d9dda2bc7ebd72fba1d674136624f968ff2f453bf7bbb894de017
  - path: scripts/core/auto-loop.sh
    hash: 9463a6ec8a9dd69c2b44cb0018168d752dd43e537e5c952f7b949e542d8b2901
  - path: tests/test_seteshape_lint.py
    hash: c75dd121edbe7aed5432f718bdfff952149464b77f9ab22baced3682261ebc98
sources_digest: 4eaee66246dbfede1855352c4ea34468d1db53797df976e55839a03b864e15c1
links:
  - to: auto-loop-core-engine
    relation: validates
    description: Lints auto-loop.sh for the fatal set -e shape.
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

A fatal bash pattern: a '[ test ] && action' list used as a function's last command or immediately before a bare return propagates a false test's exit status 1 and kills an unguarded caller under set -e — the root cause of the APP-240 incident. The lint is deliberately narrow: it does not flag done/fi/esac terminators (set -e exempts the left operand of AND-OR lists) and skips lines ending in '|| true' or '|| :', to avoid false-positives on the safe redirect-fed loop form used by docker-entrypoint.sh's runtime.env parser.

## Related

- validates [[auto-loop-core-engine]] — Lints auto-loop.sh for the fatal set -e shape.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
