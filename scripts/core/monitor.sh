#!/bin/bash
# ============================================================
# Autonomous Company — Live Monitor
# ============================================================
# Watch the auto-loop output in real-time.
#
# Usage:
#   ./monitor.sh            # Tail the main log
#   ./monitor.sh --last     # Show last cycle's full output
#   ./monitor.sh --status   # Show current loop status
#   ./monitor.sh --cycles   # Summary of all cycles
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/core/ui-messages.sh"
LOG_DIR="$PROJECT_DIR/logs"
STATE_FILE="$PROJECT_DIR/.auto-loop-state"
PID_FILE="$PROJECT_DIR/.auto-loop.pid"
PAUSE_FLAG="$PROJECT_DIR/.auto-loop-paused"
LABEL="com.autonomouscompany.loop"
OS_NAME="$(uname -s)"
HAS_LAUNCHCTL=0
HAS_SYSTEMD_USER=0

if [ "$OS_NAME" = "Darwin" ] && command -v launchctl >/dev/null 2>&1; then
    HAS_LAUNCHCTL=1
fi
if command -v systemctl >/dev/null 2>&1 && systemctl --user --version >/dev/null 2>&1; then
    HAS_SYSTEMD_USER=1
fi

case "${1:-}" in
    --status)
        echo "=== Autonomous Company Status ==="
        if [ -f "$PID_FILE" ]; then
            pid=$(cat "$PID_FILE")
            if kill -0 "$pid" 2>/dev/null; then
                echo "Loop: RUNNING (PID $pid)"
            else
                echo "Loop: STOPPED (stale PID $pid)"
            fi
        else
            echo "Loop: NOT RUNNING"
        fi

        if [ "$HAS_SYSTEMD_USER" -eq 1 ]; then
            daemon_active="$(systemctl --user is-active autonomous-company.service 2>/dev/null || true)"
            daemon_enabled="$(systemctl --user is-enabled autonomous-company.service 2>/dev/null || true)"
            if [ "$daemon_active" = "active" ]; then
                echo "Daemon: ACTIVE (systemd --user autonomous-company.service)"
            elif [ "$daemon_enabled" = "enabled" ]; then
                echo "Daemon: ENABLED but $daemon_active (systemd --user autonomous-company.service)"
            elif [ "$daemon_enabled" = "disabled" ] || [ "$daemon_enabled" = "masked" ]; then
                echo "Daemon: $daemon_enabled (systemd --user autonomous-company.service)"
            else
                echo "Daemon: NOT INSTALLED (systemd --user autonomous-company.service)"
            fi
        elif [ "$HAS_LAUNCHCTL" -eq 0 ]; then
            if [ -f "$PAUSE_FLAG" ]; then
                echo "Daemon: N/A (launchd is macOS-only; pause flag present)"
            else
                echo "Daemon: N/A (launchd is macOS-only)"
            fi
        elif [ -f "$PAUSE_FLAG" ]; then
            echo "Daemon: PAUSED (.auto-loop-paused present)"
        elif launchctl list 2>/dev/null | grep -q "$LABEL"; then
            echo "Daemon: LOADED ($LABEL)"
        else
            echo "Daemon: NOT LOADED"
        fi

        if [ -f "$STATE_FILE" ]; then
            echo ""
            cat "$STATE_FILE"
        fi

        echo ""
        echo "=== Latest Consensus ==="
        if [ -f "$PROJECT_DIR/memories/consensus.md" ]; then
            head -30 "$PROJECT_DIR/memories/consensus.md"
        else
            echo "(no consensus file)"
        fi

        echo ""
        echo "=== Recent Log ==="
        if [ -f "$LOG_DIR/auto-loop.log" ]; then
            tail -20 "$LOG_DIR/auto-loop.log"
        fi
        ;;

    --last)
        latest=$(ls -t "$LOG_DIR"/cycle-*.log 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            ui_message monitor.last "$(basename "$latest")"
            cat "$latest"
        else
            ui_message monitor.no_cycles
        fi
        ;;

    --cycles)
        ui_message monitor.cycles
        if [ -f "$LOG_DIR/auto-loop.log" ]; then
            grep -E "Cycle #[0-9]+ \[(OK|FAIL|START|LIMIT|BUDGET|BREAKER)\]" "$LOG_DIR/auto-loop.log" | tail -50
        else
            ui_message monitor.no_log
        fi
        ;;

    *)
        ui_message monitor.live "$LOG_DIR/auto-loop.log"
        echo ""
        if [ -f "$LOG_DIR/auto-loop.log" ]; then
            tail -f "$LOG_DIR/auto-loop.log"
        else
            ui_message monitor.start_first
        fi
        ;;
esac
