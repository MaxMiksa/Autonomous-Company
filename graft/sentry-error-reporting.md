---
name: Sentry Error Reporting
slug: sentry-error-reporting
type: file
sources:
  - path: dashboard/sentry_client.py
    hash: 96977bb6701f18064edb69c783e53bdb73c930c8ddadcd1caf47583b42700df4
sources_digest: d14955d1810e44ac017b77743809ea9e510da96b9f40c625eb3bfe88e5d2372d
links:
  - to: cockpit-dashboard
    relation: part_of
    description: >-
      Lives in the dashboard directory and is imported by server.py for error
      reporting
generator:
  version: 1
covers:
  - symbol: _parse_dsn
    kind: function
    at: 'dashboard/sentry_client.py:L33-L43'
  - symbol: capture_exception
    kind: function
    at: 'dashboard/sentry_client.py:L49-L102'
---
<!-- context:generated:start -->
## Summary

A minimal, stdlib-only Sentry reporter that deliberately avoids the official sentry-sdk because the container has no pip dependencies. Builds a Sentry event (stacktrace, environment, release, server name) and POSTs to the legacy Store API via urllib.request, parsing the DSN at import time. Best-effort by design: any failure is caught and logged to stderr, never raised, so monitoring can never crash the dashboard.

## Related

- part of [[cockpit-dashboard]] — Lives in the dashboard directory and is imported by server.py for error reporting
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
