# tests/test_seteshape_lint.py · [[auto-loop-core-engine]] [[set-e-shape-lint]]

Lint test that flags `[ test ] && action` shapes which, under `set -e`, return 1 when the test is false and kill an unguarded caller.

- _is_fatal_shape · function · L42-L43 — Determines whether a line is a fatal `[ ] &&` shape by matching the test-and pattern while excluding `|| true`/`|| :` safe tails.
- _executable_lines · function · L46-L52 — Filters source lines down to non-empty, non-comment executable lines with their line numbers.
- find_violations · function · L55-L84 — Scans a script for the two fatal `[ ] &&` positions: a function's last command and a line immediately before a bare return.
- SetEShapeLint · class · L87-L99 — Test case that runs the lint over the known scripts and asserts no fatal test-and shapes remain.
- test_no_fatal_test_and_shapes · method · L88-L99 — Collects violations from the target scripts and asserts the list is empty, failing with a remediation hint otherwise.
