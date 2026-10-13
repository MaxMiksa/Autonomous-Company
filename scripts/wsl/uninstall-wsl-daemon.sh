#!/bin/bash
# ============================================================
# Autonomous Company — Uninstall WSL/Linux systemd user daemon
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/core/ui-messages.sh"

SERVICE_NAME="autonomous-company.service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SERVICE_PATH="$SYSTEMD_USER_DIR/$SERVICE_NAME"

if ! command -v systemctl >/dev/null 2>&1; then
    ui_message systemd.missing
    exit 1
fi

if systemctl --user --version >/dev/null 2>&1; then
    systemctl --user disable --now "$SERVICE_NAME" >/dev/null 2>&1 || true
fi

if [ -f "$SERVICE_PATH" ]; then
    rm -f "$SERVICE_PATH"
    ui_message systemd.removed "$SERVICE_PATH"
else
    ui_message systemd.file_missing "$SERVICE_PATH"
fi

if systemctl --user --version >/dev/null 2>&1; then
    systemctl --user daemon-reload
    systemctl --user reset-failed >/dev/null 2>&1 || true
fi

ui_message systemd.uninstalled
