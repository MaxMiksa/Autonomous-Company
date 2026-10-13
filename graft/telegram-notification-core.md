---
name: Telegram Notification Core
slug: telegram-notification-core
type: file
sources:
  - path: scripts/core/telegram-notify.sh
    hash: a6b475c3d6e94b205066d93a4054681477be96876b0f8eac60b47f13ab2573ef
sources_digest: 3dc173f8889cdab53470b50d79d2518beedb357a6bcbc9c68f009fdbd555a439
links:
  - to: operator-alerting-watchers
    relation: implements
    description: >-
      The contract that registry-queue-watch, reply-watch, and rfq-reply-watch
      shell out to for notifications.
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/core/telegram-notify.sh is the shared notification sink that all operator alerting watchers and escalation scripts shell out to, with tokens loaded from logs/runtime.env. It is the single delivery path for Telegram alarms across the ops tooling.

## Related

- implements [[operator-alerting-watchers]] — The contract that registry-queue-watch, reply-watch, and rfq-reply-watch shell out to for notifications.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
