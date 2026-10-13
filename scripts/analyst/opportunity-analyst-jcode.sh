#!/usr/bin/env bash
# Opportunity Analyst — jcode variant. THE live path since the 2026-07-31 cutover
# (host cron ENGINE default is jcode); opportunity-analyst.sh (codex CLI) is legacy.
# Default engine since 2026-08-03: jcode provider `claude`; model `claude-opus-5-5` since
# 2026-10-12 (was claude-opus-5; operator 08-03: "Codex'i unut şimdilik, kendi analistimizi opus ile kuracağız").
# Manual run:
#   docker exec -u app <container> bash /app/scripts/analyst/opportunity-analyst-jcode.sh
#
# Behavioral contract is identical to opportunity-analyst.sh — same inputs, same
# three passes, same outputs (analysis-directive.md draft / registry live-span merge /
# deterministic promotion gate), same REPORT_OK protocol, same directive-restore
# guardrail. What changed and WHY:
#
#   engine        codex exec --json -o msg        ->  jcode run --ndjson (final text
#                 (message written to a file)         extracted from the `done` event)
#   skill         $skill from CODEX_HOME          ->  the model READS the repo skill
#                 (synced every run — a stale-        file itself. One source of truth,
#                 copy bug lived here once)           no sync step to go stale.
#   effort        -c model_reasoning_effort=X     ->  JCODE_<PROVIDER>_REASONING_EFFORT=X
#                                                     (openai vs anthropic env, same
#                                                     case as auto-loop.sh's jcode path)
#   model check   (codex validated -m)            ->  EXPLICIT preflight against
#                                                     `jcode model list` — jcode
#                                                     SILENTLY substitutes its default
#                                                     model for an unknown -m (measured
#                                                     2026-07-31; the ladder must never
#                                                     inherit that trap)
#   sandbox       -c sandbox_mode=...             ->  none; container isolation + the
#                                                     skill's no-write instruction +
#                                                     the directive snapshot/restore
#   budget        thread_id -> analyst-codex-     ->  session_id (done event) ->
#                 sessions.log (ccusage exclude)      analyst-jcode-sessions.log, same
#                                                     fail-closed direction. jcode runs
#                                                     never appear in CODEX_HOME, so
#                                                     ccusage cannot MIS-attribute them;
#                                                     the ledger exists for the future
#                                                     jcode-native accounting.
#   cost line     (implicit in ccusage)           ->  engine-usage-cost.py on the
#                                                     ndjson, logged to progress. For
#                                                     gpt-5.6-sol this is an ESTIMATED
#                                                     figure until the price row is
#                                                     calibrated (gate 4/5) — logged,
#                                                     never gated on.
set -uo pipefail

APP="${APP_DIR:-/app}"
# 2026-08-24 Wowcar re-charter: the analyst is retargeted from the (frozen) Tender
# Track to the Wowcar 2.0 program. Old skill dir kept as history; runner no longer
# reads it. Registry merge (old pass-2) and directive promotion (old pass-3) are
# RETIRED in this mode — the auditor writes nothing and produces no directive.
SKILL_MD="$APP/scripts/analyst/codex-skill/${ANALYST_SKILL:-wowcar-program-auditor}/SKILL.md"
REGISTRY="$APP/memories/candidate-registry.md"
CONSENSUS="$APP/memories/consensus.md"
OUT_DIRECTIVE="$APP/memories/analysis-directive.md"
PROGRESS="$APP/memories/analyst-progress.md"

JCODE_BIN="$(command -v jcode || echo /usr/local/bin/jcode)"
# Engine switched to Opus by operator decision 2026-08-03 ("Codex'i unut şimdilik,
# kendi analistimizi opus ile kuracağız"). jcode's provider name for the Claude
# native-credential path is `claude` (NOT `anthropic` — that value does not exist;
# `anthropic-api` is the raw-API variant). The Codex path stays reachable via
# ANALYST_PROVIDER=openai ANALYST_MODEL=gpt-5.6-sol.
PROVIDER="${ANALYST_PROVIDER:-claude}"
MODEL="${ANALYST_MODEL:-claude-opus-5-5}"
# Operator caps effort at "high" — respect it; do not override the default.
EFFORT="${ANALYST_EFFORT:-high}"
# 1500 -> 2400 (2026-10-12): the first claude-opus-5-5 canary pass was killed by `timeout` at
# exactly 1500 s mid tool-call (no done event -> priced as UNKNOWN MODEL x5), and only the
# retry pass finished (19 min). Opus 5.5 at effort=high reads more before writing; 40 min
# keeps a single pass inside the window. Weekly cadence makes the extra wall time cheap.
TIMEOUT="${ANALYST_TIMEOUT:-2400}"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
JQUIET=(--quiet --no-update --no-selfdev)
export JCODE_NO_TELEMETRY=1
JHOME="${JCODE_HOME:-$HOME/.jcode}"

log() { printf '%s\n' "$1" >> "$PROGRESS"; }
fail() { log "[$STAMP] ANALYST_FAILED: $1"; echo "ANALYST_FAILED: $1" >&2; exit 1; }

# --- preconditions ---
for f in "$APP/memories/human-directive.md" "$CONSENSUS" "$SKILL_MD"; do [ -f "$f" ] || fail "missing input: $f"; done
[ -x "$JCODE_BIN" ] || fail "jcode not found"
# Auth is PROVIDER-SHAPED, not one rule:
#   openai -> a jcode login file (measured gate 4, 2026-07-31: `jcode login openai`
#             writes ~/.jcode/openai-auth.json — there is no generic auth.json).
#   claude -> the loop's own credential: CLAUDE_CODE_OAUTH_TOKEN (or ANTHROPIC_API_KEY)
#             through the claude_code_native_credentials trust. The one-shot analyst
#             container has entrypoint=sleep, so nothing sourced runtime.env for us —
#             read ONLY the needed key, literally (no shell-eval of the whole file,
#             no echo of the value anywhere).
if [ "$PROVIDER" = "openai" ]; then
  [ -s "$JHOME/openai-auth.json" ] \
    || fail "jcode openai-auth.json missing (run: jcode login --provider openai — operator step, gate 4)"
else
  if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ] && [ -f "$APP/logs/runtime.env" ]; then
    CLAUDE_CODE_OAUTH_TOKEN="$(sed -n 's/^CLAUDE_CODE_OAUTH_TOKEN=//p' "$APP/logs/runtime.env" | head -1)"
    export CLAUDE_CODE_OAUTH_TOKEN
  fi
  [ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] || [ -n "${ANTHROPIC_API_KEY:-}" ] || [ -s "$JHOME/claude-auth.json" ] \
    || fail "no Claude credential: CLAUDE_CODE_OAUTH_TOKEN/ANTHROPIC_API_KEY unset and no $JHOME/claude-auth.json (is /app/logs/runtime.env mounted?)"
  # jcode cannot read a BARE sk-ant-oat… token — it parses it as an expired OAuth
  # credential and dies with "token is expired and no usable refresh token" (measured
  # 2026-08-03, three failed runs). The loop hit the same wall and wraps the token in
  # a claudeAiOauth JSON envelope with a synthetic expiry just before invoking jcode
  # (auto-loop.sh, "claudeAiOauth wrapper" note). Same wrapper here, same reason; the
  # raw token is never echoed and the wrapped form lives only in this process.
  case "${CLAUDE_CODE_OAUTH_TOKEN:-}" in
    sk-ant-oat*)
      _jc_exp=$(( ($(date +%s) + 86400*300) * 1000 ))
      _jc_tok=$(python3 -c 'import json,os,sys; print(json.dumps({"claudeAiOauth":{"accessToken":os.environ["CLAUDE_CODE_OAUTH_TOKEN"],"refreshToken":"","expiresAt":int(sys.argv[1]),"scopes":["user:inference"],"subscriptionType":"max"}}))' "$_jc_exp" 2>/dev/null || true)
      [ -n "$_jc_tok" ] && export CLAUDE_CODE_OAUTH_TOKEN="$_jc_tok"
      unset _jc_tok _jc_exp
      ;;
  esac
fi
grep -q claude_code_native_credentials "$JHOME/config.toml" 2>/dev/null || {
  mkdir -p "$JHOME"
  printf '[auth]\ntrusted_external_sources = ["claude_code_native_credentials"]\n' >> "$JHOME/config.toml"
}

# Model preflight — the silent-fallback trap. An unknown -m does NOT error; jcode
# quietly runs its default model instead. Fail loudly here, never discover it in
# the usage ledger a week later.
"$JCODE_BIN" "${JQUIET[@]}" model list -p "$PROVIDER" 2>/dev/null | grep -qx "$MODEL" \
  || fail "model '$MODEL' not in 'jcode model list -p $PROVIDER' — refusing (jcode would silently substitute its default)"

WORK="$(mktemp -d)"
# Persist the raw ndjson event streams before the workdir dies — they are the
# only source for price calibration / cost audits (the 5x-estimate era ended
# because no run had kept one). Last 5 runs, pruned oldest-first.
NDJSON_KEEP="$APP/logs/analyst-ndjson"
persist_ndjson() {
  mkdir -p "$NDJSON_KEEP/$STAMP" 2>/dev/null || return 0
  cp "$WORK"/*.ndjson "$NDJSON_KEEP/$STAMP/" 2>/dev/null || true
  ls -dt "$NDJSON_KEEP"/*/ 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true
}
trap 'persist_ndjson; rm -rf "$WORK"' EXIT
MSG="$WORK/msg.txt"

# Deterministic cost audit, refreshed immediately before the analyst reads it. The
# analyst INTERPRETS these numbers and must never recompute them: a high-effort model
# doing arithmetic over log files is both expensive and able to produce a plausible
# wrong number. Non-fatal by design — a failed audit costs the report one section, it
# must never cost the run.
# -f, not -x: the file ships mode 644 (the Dockerfile chmods only scripts/core and
# scripts/linux), so an -x guard silently skipped the audit on EVERY run — and because
# the failure NOTE lived inside the same guard, nothing was ever logged about it.
# Found by the analyst itself (first opus run, 2026-08-03, FINDING B).
if [ -f "$APP/scripts/ops/cost-audit.py" ]; then
  if python3 "$APP/scripts/ops/cost-audit.py" --app "$APP" >>"$PROGRESS" 2>&1; then
    log "[$STAMP] cost audit refreshed (memories/cost-audit.md)"
  else
    log "[$STAMP] NOTE: cost audit failed — the report's cost section will say NOT MEASURED"
  fi
fi
# Staleness measurements (2026-10-13): deterministic, read-only; the skill's step 6b
# interprets them. Failure is logged, never fatal — the report then says NOT MEASURED.
if [ -f "$APP/scripts/ops/staleness-report.py" ]; then
  if python3 "$APP/scripts/ops/staleness-report.py" --app "$APP" >>"$PROGRESS" 2>&1; then
    log "[$STAMP] staleness report refreshed (memories/staleness-report.md)"
  else
    log "[$STAMP] NOTE: staleness report failed — the report's staleness section will say NOT MEASURED"
  fi
fi

read -r -d '' PROMPT <<EOF
FIRST, read $SKILL_MD in full and adopt it as your operating skill for this task —
including any files under its references/ directory that it tells you to consult.
Then, following that skill exactly, independently AUDIT Auto Company's Wowcar 2.0
establishment program and produce the audit report.

Inputs are in this workspace ($APP) — find them with rg:
- memories/human-directive.md   (ANA DİREKTİF — the charter; outranks your judgment on scope)
- memories/consensus.md         (the company's own current reading + Program State)
- projects/wowcar/              (the five source documents, SHA-256s recorded in the directive)
- projects/wowcar/Wowcar_Sponsor_Kararlari.md  (sponsor's BINDING decisions KARAR-*; they SUPERSEDE the source docs' open questions — e.g. legal form is direction-decided here. Do NOT re-flag a decided question; mark it "direction-set, condition open". A declaration sets direction, not legal evidence.)
- memories/operator-decisions.md               (resolved operator/OPREQ decisions; same supersession rule)
- docs/operations/              (receipts, ledgers, weekly reports, gate artifacts)
- memories/cost-audit.md        (TODAY's deterministic cost measurements — interpret, never recompute; if missing or stale, say so)
- memories/staleness-report.md  (TODAY's deterministic staleness flags — skill step 6b: ARŞİVLE / BIRAK / SOR per flagged row; interpret, never recompute)

STANDING SCOPE (operator re-charter, 2026-08-24): the company's ONLY mission is the
Wowcar 2.0 program. The Tender Track and the candidate registry are FROZEN HISTORICAL
STATE — never analyze, rank, revive, or summarize them beyond noting they are frozen.
You never produce a paste-ready directive; steering is the operator's alone.

Do NOT write or modify any files yourself — output your full audit report as your final message, following the skill's output order.
EOF

# Budget-exclusion ledger (jcode side). Failure records nothing — an uncaptured
# analyst session counts toward company totals, the mandated fail-closed direction.
ANALYST_SESSIONS_FILE="$APP/logs/analyst-jcode-sessions.log"
record_analyst_session() { # $1=ndjson events file
  python3 - "$1" "$ANALYST_SESSIONS_FILE" <<'PY' 2>/dev/null || true
import json, sys, time
events_p, ledger_p = sys.argv[1], sys.argv[2]
sid = None
with open(events_p, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("type") == "done" and ev.get("session_id"):
            sid = str(ev["session_id"])
if not sid:
    sys.exit(0)
try:
    existing = open(ledger_p, encoding="utf-8").read()
except FileNotFoundError:
    existing = ""
if sid in existing:
    sys.exit(0)
with open(ledger_p, "a", encoding="utf-8") as fh:
    fh.write(f"{int(time.time())} {sid}\n")
PY
}

# Extract the final assistant text from an ndjson stream into a file.
# The `done` event's .text is the whole final message; `-o`-style output files
# do not exist in jcode. Exit 1 (leaving the output empty) if no done event.
# Delegates to the ONE extractor (scripts/core/jcode-final-text.py). This used to read
# `done.text` directly, which is the last text BLOCK rather than the answer — measured
# 2026-07-31. It never bit the analyst (its 42k-char reports came through done.text
# whole, and the <200-char guard would not have caught a half-lost 42k report either),
# but the failure is silent by construction, so both callers now share one reading.
extract_final_text() { # $1=ndjson file  $2=out file
  python3 "$APP/scripts/core/jcode-final-text.py" "$1" > "$2" 2>/dev/null
  [ -s "$2" ]
}

log_run_cost() { # $1=ndjson file $2=label — visibility only, never gating
  local cost
  cost="$(python3 "$APP/scripts/core/engine-usage-cost.py" --ndjson-file "$1" 2>/dev/null)" \
    && log "[$STAMP] COST $2: $cost" \
    || log "[$STAMP] COST $2: unavailable (adapter error — run counts toward company totals)"
}

run_jcode() { # $1=effort $2=prompt $3=events-out $4=text-out
  # jcode `run` has no stdin/file transport: the prompt rides argv, and Linux caps a
  # single argument at 131072 bytes (E2BIG surfaces as an unexplained rc=126 — this
  # killed loop cycles #7/#8 on 2026-07-31). Pass-1 here is a ~1.7KB by-reference
  # bootstrap and pass-2 embeds only the registry live span (~8KB measured), so this
  # guard should never fire — it exists so growth fails LOUDLY instead of as rc=126.
  local _pb; _pb=$(printf '%s' "$2" | wc -c | tr -d ' ')
  if [ "${_pb:-0}" -ge 126000 ]; then
    log "[$STAMP] PROMPT-TOO-LARGE: jcode argv prompt is ${_pb} bytes (>=126000; kernel per-arg cap 131072) — refusing before exec dies rc=126"
    return 1
  fi
  # Effort rides a PROVIDER-NAMED env var — same case as auto-loop.sh's jcode path
  # (openai -> JCODE_OPENAI_REASONING_EFFORT, everything else -> the anthropic one).
  local _effort_env="JCODE_ANTHROPIC_REASONING_EFFORT"
  [ "$PROVIDER" = "openai" ] && _effort_env="JCODE_OPENAI_REASONING_EFFORT"
  ( cd "$APP" && env "$_effort_env=$1" timeout "$TIMEOUT" \
      "$JCODE_BIN" -p "$PROVIDER" -m "$MODEL" -C "$APP" run "$2" \
      "${JQUIET[@]}" --ndjson ) >"$3" 2>"$3.err"
  local rc=$?
  record_analyst_session "$3"
  extract_final_text "$3" "$4" || return 1
  return $rc
}

# --- draft-only guardrail: the analyst must never modify the live directive ---
DIRECTIVE_LIVE="$APP/memories/human-directive.md"
DIRECTIVE_BAK=""
if [ -f "$DIRECTIVE_LIVE" ]; then DIRECTIVE_BAK="$WORK/human-directive.bak"; cp "$DIRECTIVE_LIVE" "$DIRECTIVE_BAK"; fi
DIRECTIVE_SHA=""
[ -n "$DIRECTIVE_BAK" ] && DIRECTIVE_SHA=$(sha256sum "$DIRECTIVE_LIVE" 2>/dev/null | cut -d' ' -f1)

restore_directive() {
  [ -n "$DIRECTIVE_BAK" ] || return 0
  AC_APP_DIR="$APP" AC_ACTOR="opportunity-analyst-jcode" \
  python3 "$APP/scripts/core/directive_writer.py" restore \
      --from-file "$DIRECTIVE_BAK" --expect-sha256 "${DIRECTIVE_SHA:-none}" \
      >>"$PROGRESS" 2>&1 \
    || log "[$STAMP] NOTE: directive restore refused (the slot was written during the analyst run) — live file left alone, candidate kept in memories/human-directive-recovery/"
}

USED_EFFORT="$EFFORT"
run_jcode "$EFFORT" "$PROMPT" "$WORK/ev1.ndjson" "$MSG"; rc=$?
if [ "$rc" -ne 0 ] || [ ! -s "$MSG" ]; then
  log "[$STAMP] jcode run failed (rc=$rc); one retry at effort='$EFFORT'"
  run_jcode "$EFFORT" "$PROMPT" "$WORK/ev1b.ndjson" "$MSG"; rc=$?
fi
restore_directive
[ "$rc" -eq 0 ] && [ -s "$MSG" ] || fail "jcode produced no output (rc=$rc); tail: $(tail -3 "$WORK/ev1.ndjson.err" 2>/dev/null | tr '\n' ' ')"
log_run_cost "$WORK/ev1.ndjson" "pass-1"

# --- PASS 1 dispose: write the full decision report to analysis-directive.md ---
python3 - "$MSG" "$OUT_DIRECTIVE" "$PROGRESS" "$STAMP" "$MODEL" "$USED_EFFORT" "$PROVIDER" <<'PY' || fail "report post-processing failed"
import sys
msg_p, out_p, prog, stamp, model, effort, provider = sys.argv[1:8]
report = open(msg_p, encoding="utf-8").read().strip()
if len(report) < 200:
    open(prog,"a",encoding="utf-8").write(f"[{stamp}] ANALYST_FAILED: report too short ({len(report)} chars)\n"); sys.exit(1)
doc = (f"# Wowcar Program Audit — {stamp}\n\n"
       f"*Engine: jcode/{provider} `{model}` · effort `{effort}` · skill `wowcar-program-auditor` (read from repo) · mode: AUDIT-ONLY (no registry write, no promotion)*\n\n"
       f"---\n\n{report}\n")
open(out_p,"w",encoding="utf-8").write(doc)
open(prog,"a",encoding="utf-8").write(f"[{stamp}] REPORT OK | engine=jcode/{provider} model={model} effort={effort} | report={len(report)}c\n")
print("REPORT_OK")
PY

# --- PASS 2 (registry merge) and PASS 3 (directive promotion): RETIRED 2026-08-24.
# The Wowcar auditor writes nothing and never produces a promotable directive, so both
# disposal passes are gone with the Tender Track. Their history lives in git; restoring
# them is a deliberate operator decision, not a flag flip.

echo "Wowcar Program Auditor (jcode) run complete ($STAMP) — report written to $OUT_DIRECTIVE."
