---
name: Business-Hours & Window Gating
slug: business-hours-window-gating
type: concept
sources:
  - path: tests/test_active_window.sh
    hash: fcd17dad9794b155cb623d85a88dd74bf10c12961df71a37f446f030958135fd
  - path: tests/test_auto_loop_work_window.sh
    hash: 7bb4ebdcaef7c71820540195fab59c8c657ff11f525429105bb0376a30405369
sources_digest: ba12d312dcdd0610440f53f1b235f3d62d320ed0f227698dadb4eeebfaccd40a
links:
  - to: fail-closed-harness-brakes
    relation: implements
    description: Window gating is part of the harness braking contract
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

The _window_active() business-hours gate and work-window logic extracted from auto-loop.sh: handles the octal trap of leading zeros (08/09), midnight-wrapping windows (22-06), and fails open on malformed/missing config so a typo never parks the company. Wiring order matters — _window_active must run before select_cycle_engine and before loop_count increment so off-hours ticks don't burn cycle numbers or trigger external calls, with a 900s off-hours poll default.

## Related

- implements [[fail-closed-harness-brakes]] — Window gating is part of the harness braking contract
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
