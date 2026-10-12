---
name: Context7 import audit
slug: context7-import-audit
type: file
sources:
  - path: tests/test_context7_check.sh
    hash: d4fc93cf6b456038f23e1e756019a7fa1b47a344b0385bc5cd3d3a5536834733
sources_digest: 0491c4407e0fe69bcc8291502ec69f7a3a70a54cb2d14a35aae791d02d5557e2
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/ops/context7-check.py audits AI assistant cycles to ensure external library imports are accompanied by a Context7 documentation lookup, flagging violations as CONTEXT7 NO-CHECK and naming the module. Must not fire on the project's own ops scripts (stdlib only) to avoid false alarms that erode trust; parses payloads via JSON not regex to handle escaped quotes/newlines; reports scoped npm packages as @scope/pkg.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
