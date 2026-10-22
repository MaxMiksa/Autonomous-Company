#!/bin/bash
# Host orchestration inside auto-loop's original admission/governance/lock.
HARNESS_TOOL="$SCRIPT_DIR/company_harness_runner.py"
HARNESS_BRIDGE_PID=""
CURRENT_HARNESS_ATTEMPT=""
HARNESS_FINAL_ACTION=""
HARNESS_CLOSED=""
HARNESS_GOVERNANCE_BLOCKED=0
HARNESS_STOPPED_BRIDGE_PID=""

harness_bridge_stop() {
    if [ -n "$HARNESS_BRIDGE_PID" ]; then
        kill -TERM "$HARNESS_BRIDGE_PID" 2>/dev/null || true
        wait "$HARNESS_BRIDGE_PID" 2>/dev/null || true
        HARNESS_STOPPED_BRIDGE_PID="$HARNESS_BRIDGE_PID"
        HARNESS_BRIDGE_PID=""
    fi
}

harness_close_cycle() {
    local governance_ok="$1" capture
    capture=$(mktemp)
    cycle_supervisor_run "${COMPANY_HARNESS_CLOSE_SECONDS:-60}" "$CYCLE_TERM_GRACE_SECONDS" "$CYCLE_KILL_WAIT_SECONDS" \
        "$PROJECT_DIR" "$capture" -- python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" close \
        --cycle "$CURRENT_PRODUCT_CYCLE_ID" --governance-ok "$governance_ok" || true
    if [ "$CYCLE_SUPERVISOR_CLEANUP_FAILED" -ne 0 ] || [ "$CYCLE_SUPERVISOR_TIMED_OUT" -ne 0 ] || [ "$CYCLE_SUPERVISOR_EXIT_CODE" -ne 0 ]; then
        cat "$capture" >&2
        rm -f "$capture"
        return 1
    fi
    HARNESS_CLOSED=$(cat "$capture")
    rm -f "$capture"
}

harness_run_cycle() {
    local base_prompt="$1" original_log="$cycle_log" original_timeout="$CYCLE_TIMEOUT_SECONDS"
    local original_sandbox="$CODEX_SANDBOX_MODE" attempt_fields attempt_timeout recovery ready tries action guard_status
    python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" prepare --cycle "$CURRENT_PRODUCT_CYCLE_ID" >/dev/null || cleanup 1 harness_contract_invalid
    HARNESS_FINAL_ACTION="human"
    HARNESS_GOVERNANCE_BLOCKED=0
    while true; do
        center_admission_check || cleanup 1 center_admission_lost
        check_stop_requested && cleanup 0 stopped
        set +e
        "$CONSENSUS_GUARD" admit-attempt "$loop_count"
        guard_status=$?
        set -e
        if [ "$guard_status" -ne 0 ]; then
            HARNESS_GOVERNANCE_BLOCKED=1
            HARNESS_FINAL_ACTION=human
            break
        fi
        if ! attempt_fields=$(python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" attempt --cycle "$CURRENT_PRODUCT_CYCLE_ID"); then
            break
        fi
        read -r CURRENT_HARNESS_ATTEMPT attempt_timeout recovery <<< "$attempt_fields"
        export AUTONOMOUS_COMPANY_ATTEMPT_ID="$CURRENT_HARNESS_ATTEMPT"
        export COMPANY_HARNESS_MANIFEST="$PROJECT_DIR/.autonomous-company/harness/$CURRENT_HARNESS_ATTEMPT.json"
        ready=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["ready"])' "$COMPANY_HARNESS_MANIFEST")
        python3 "$SCRIPT_DIR/company_harness_bridge.py" --root "$PROJECT_DIR" --manifest "$COMPANY_HARNESS_MANIFEST" &
        HARNESS_BRIDGE_PID=$!
        tries=0
        while [ ! -f "$ready" ]; do
            if ! kill -0 "$HARNESS_BRIDGE_PID" 2>/dev/null || [ "$tries" -ge 100 ]; then
                cleanup 1 harness_bridge_unavailable
            fi
            tries=$((tries + 1))
            loop_sleep 0.05
        done
        cycle_log="$LOG_DIR/$CURRENT_HARNESS_ATTEMPT.log"
        CODEX_SANDBOX_MODE="$original_sandbox"
        export CODEX_SANDBOX_MODE
        harness_prompt=$(python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" prompt --attempt "$CURRENT_HARNESS_ATTEMPT")
        if ! CYCLE_TIMEOUT_SECONDS=$(python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" dispatch --attempt "$CURRENT_HARNESS_ATTEMPT"); then
            harness_bridge_stop || cleanup 1 harness_writer_unconfirmed
            python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" unstarted --attempt "$CURRENT_HARNESS_ATTEMPT" \
                --bridge-pid "$HARNESS_STOPPED_BRIDGE_PID" >/dev/null || cleanup 1 harness_predispatch_unconfirmed
            HARNESS_FINAL_ACTION=retry
            continue
        fi
        engine_adapter_run "$base_prompt
$harness_prompt"
        harness_bridge_stop
        if [ "$CYCLE_SUPERVISOR_CLEANUP_FAILED" -ne 0 ] || [ "${ADAPTER_LOG_FAILED:-0}" -ne 0 ]; then
            cleanup 1 harness_writer_unconfirmed
        fi
        printf '%s\n' "$ADAPTER_OUTPUT" > "$cycle_log"
        engine_adapter_extract_metadata
        engine_adapter_write_record "${cycle_log%.log}.json" "$ADAPTER_STATUS"
        if ! action=$(python3 "$HARNESS_TOOL" --root "$PROJECT_DIR" finish --attempt "$CURRENT_HARNESS_ATTEMPT" \
            --metadata "${cycle_log%.log}.json" --cleanup-failed "$CYCLE_SUPERVISOR_CLEANUP_FAILED" \
            --supervisor-owner "$CYCLE_SUPERVISOR_LAST_PGID"); then
            cleanup 1 harness_settlement_failed
        fi
        set +e
        "$CONSENSUS_GUARD" verify "$loop_count"
        guard_status=$?
        set -e
        HARNESS_FINAL_ACTION="$action"
        [ "$guard_status" -eq 0 ] || break
        [ "$action" = retry ] || break
    done
    CYCLE_TIMEOUT_SECONDS="$original_timeout"
    CODEX_SANDBOX_MODE="$original_sandbox"
    export CODEX_SANDBOX_MODE
    cycle_log="$original_log"
    unset AUTONOMOUS_COMPANY_ATTEMPT_ID COMPANY_HARNESS_MANIFEST
    # No provider-level success is allowed to stand in for protocol success.
    local final_outcome
    final_outcome=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["outcome"])' "$PROJECT_DIR/.autonomous-company/harness/$CURRENT_PRODUCT_CYCLE_ID.result.json")
    if [ "$HARNESS_FINAL_ACTION" != close ] || { [ "$final_outcome" != completed ] && [ "$final_outcome" != partial ]; }; then
        ADAPTER_STATUS=error
        ADAPTER_EXIT_CODE=78
        ADAPTER_SUBTYPE=harness_needs_human
    fi
}
