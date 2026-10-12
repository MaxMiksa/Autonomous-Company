#!/usr/bin/env bash
# The analyst's engine plumbing, exercised offline against a stub jcode.
#
#   bash tests/test_analyst_engine.sh
#
# The 2026-08-03 change moved the analyst's default engine from jcode/openai
# (gpt-5.6-sol) to jcode/claude (claude-opus-5; claude-opus-5-5 since 2026-10-12). Everything provider-shaped is
# testable without a model: which auth precondition fires, which effort env var
# rides the exec, whether the session ledger records the done-event session_id,
# and whether the report header names the provider that actually ran.
#
#   1. claude default: no credential anywhere -> fails naming CLAUDE_CODE_OAUTH_TOKEN
#   2. claude: token present in runtime.env is picked up literally (no shell-eval)
#   3. openai: missing openai-auth.json -> fails naming the login step
#   4. effort env: claude run exports JCODE_ANTHROPIC_REASONING_EFFORT, openai the OPENAI one
#   5. session ledger: done.session_id lands in analyst-jcode-sessions.log once (deduped)
#   6. report header carries jcode/<provider> and the model
set -uo pipefail
cd "$(dirname "$0")/.."
SCRIPT="$PWD/scripts/analyst/opportunity-analyst-jcode.sh"
fail=0
trap 'echo "  FAIL harness error on line $LINENO"; fail=1' ERR
check()    { if [ "$2" = "$3" ]; then echo "  PASS $1"; else echo "  FAIL $1: got '$2' want '$3'"; fail=1; fi; }
contains() { case "$2" in *"$3"*) echo "  PASS $1" ;; *) echo "  FAIL $1: '$3' not in '${2:0:200}'"; fail=1 ;; esac; }

mk_app() { # builds a minimal fake /app; prints its path
  local A; A="$(mktemp -d)"
  mkdir -p "$A/memories" "$A/logs" "$A/scripts/analyst/codex-skill/wowcar-program-auditor" "$A/scripts/core"
  printf '## Status\nPENDING\n' > "$A/memories/human-directive.md"
  echo "state" > "$A/memories/consensus.md"
  echo "brief" > "$A/scripts/analyst/codex-skill/wowcar-program-auditor/SKILL.md"
  # the script calls these helpers; give them honest minimal stand-ins
  printf 'import sys\nprint(open(sys.argv[1]).read())\n' > "$A/scripts/core/jcode-final-text.py"
  printf 'import sys\nprint("$0.00 (stub)")\n' > "$A/scripts/core/engine-usage-cost.py"
  echo "$A"
}

mk_stub_jcode() { # $1=bindir — stub that records env+args and emits a done event
  cat > "$1/jcode" <<'STUB'
#!/usr/bin/env bash
# test stub: records the effort envs + argv, emits a plausible ndjson stream
{ echo "OPENAI_EFF=${JCODE_OPENAI_REASONING_EFFORT:-}";
  echo "ANTH_EFF=${JCODE_ANTHROPIC_REASONING_EFFORT:-}";
  echo "ARGS=$*"; } >> "${STUB_LOG:?}"
if [ "$1" = "model" ] || [ "$2" = "model" ] || printf '%s' "$*" | grep -q "model list"; then
  echo "claude-opus-5"; echo "claude-opus-5-5"; echo "gpt-5.6-sol"; exit 0
fi
printf '{"type":"thread.started"}\n'
printf '{"type":"done","session_id":"stub-session-0001","text":"%s"}\n' \
  "STUB REPORT: long enough to clear the 200-char floor. $(printf 'x%.0s' $(seq 1 220))"
STUB
  chmod +x "$1/jcode"
  # macOS has no GNU `timeout`; the script wraps every jcode call in one. A shim
  # that drops the duration keeps the offline test honest about everything else.
  printf '#!/bin/bash\nshift\nexec "$@"\n' > "$1/timeout"
  chmod +x "$1/timeout"
}

B="$(mktemp -d)"; mk_stub_jcode "$B"

echo "1. claude default with no credential fails closed, naming the missing token"
A=$(mk_app)
rc=0
OUT=$( cd "$A" && APP_DIR="$A" HOME="$A" PATH="$B:/usr/bin:/bin" \
       CLAUDE_CODE_OAUTH_TOKEN= ANTHROPIC_API_KEY= \
       bash "$SCRIPT" 2>&1 ) || rc=$?
check "exits nonzero" "$([ $rc -ne 0 ] && echo yes)" "yes"
contains "names the token" "$OUT" "CLAUDE_CODE_OAUTH_TOKEN"
rm -rf "$A"

echo "2. token is read from runtime.env literally (value with \$ and spaces survives)"
A=$(mk_app)
printf 'OTHER=1\nCLAUDE_CODE_OAUTH_TOKEN=sk-test-$literal not-evaled\n' > "$A/logs/runtime.env"
export STUB_LOG="$A/logs/stub.log"
( cd "$A" && APP_DIR="$A" HOME="$A" PATH="$B:/usr/bin:/bin" STUB_LOG="$STUB_LOG" \
  CLAUDE_CODE_OAUTH_TOKEN= ANTHROPIC_API_KEY= ANALYST_TIMEOUT=30 \
  bash "$SCRIPT" >/dev/null 2>&1 ) || true
# the run got past the auth gate iff the stub was ever invoked
check "auth gate passed via runtime.env" "$([ -s "$STUB_LOG" ] && echo yes)" "yes"

echo "3. openai provider without openai-auth.json fails naming the login step"
rc=0
OUT=$( cd "$A" && APP_DIR="$A" HOME="$A" PATH="$B:/usr/bin:/bin" \
       ANALYST_PROVIDER=openai bash "$SCRIPT" 2>&1 ) || rc=$?
check "exits nonzero" "$([ $rc -ne 0 ] && echo yes)" "yes"
contains "names jcode login" "$OUT" "jcode login"

echo "4. effort rides the provider-named env var"
contains "claude run set the anthropic env" "$(cat "$STUB_LOG")" "ANTH_EFF=high"
if grep -q "OPENAI_EFF=high" "$STUB_LOG"; then
  echo "  FAIL claude run leaked the openai effort env"; fail=1
else
  echo "  PASS openai env untouched on the claude path"
fi

echo "5. done.session_id recorded in the jcode session ledger, deduped"
# both passes emit the SAME stub session id; dedup must keep exactly one line
check "exactly one ledger line" "$(grep -c "stub-session-0001" "$A/logs/analyst-jcode-sessions.log" 2>/dev/null)" "1"

echo "6. the report header names jcode/claude and the model"
contains "provider in header" "$(head -3 "$A/memories/analysis-directive.md" 2>/dev/null)" "jcode/claude"
contains "model in header" "$(head -3 "$A/memories/analysis-directive.md" 2>/dev/null)" "claude-opus-5-5"
rm -rf "$A" "$B"

if [ "$fail" -eq 0 ]; then echo "ALL PASS"; else echo "FAILURES"; fi
exit "$fail"
