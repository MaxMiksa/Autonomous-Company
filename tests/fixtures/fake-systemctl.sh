#!/bin/bash
# Isolated dashboard adapter fixture: never forwards to real systemctl.
case "$*" in
    *--version*|*show-environment*) exit 0 ;;
    *'cat autonomous-company.service'*) [ "${FAKE_SERVICE_MISSING:-0}" != 1 ]; exit $? ;;
    *WorkingDirectory*) printf '%s\n' "$FAKE_SERVICE_ROOT" ;;
    *MainPID*) printf '0\n' ;;
    *ControlGroup*) printf '\n' ;;
    *SubState*) printf 'dead\n' ;;
    *is-active*)
        if [ -f "$FAKE_SERVICE_LOG" ] && [ "$(tail -1 "$FAKE_SERVICE_LOG")" = stop ]; then
            printf 'inactive\n'
        else
            printf '%s\n' "$FAKE_SERVICE_STATE"
        fi
        ;;
    *is-enabled*) printf '%s\n' "$FAKE_SERVICE_ENABLED" ;;
    *'start autonomous-company.service'*) printf 'start\n' >> "$FAKE_SERVICE_LOG" ;;
    *'stop autonomous-company.service'*) printf 'stop\n' >> "$FAKE_SERVICE_LOG" ;;
    *) printf 'Unexpected systemctl fixture arguments: %s\n' "$*" >&2; exit 1 ;;
esac
