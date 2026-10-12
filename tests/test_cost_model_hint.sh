#!/usr/bin/env bash
# Regression tests for the killed-cycle model hint (scripts/core/engine-usage-cost.py).
#
#   bash tests/test_cost_model_hint.sh
#
# Why this exists: a watchdog-killed cycle produces a stream with REAL token events but
# NO `done` event, so the adapter had no model name and priced at the unknown-model row
# × 5.0. Measured 2026-08-01: one timed-out cycle booked $63.63 against a real ~$12.7 and
# filled 64% of the 5h Claude window by itself, which suppressed the effort ladder for
# hours. The hint fixes that WITHOUT loosening the fail-closed guarantees, and these
# tests pin exactly where the line is:
#   1. no hint + no done          -> conservative row (unchanged)
#   2. valid hint + no done       -> real tariff, estimated:true, basis says HINT
#   3. UNRECOGNISED hint + no done-> still conservative (a bad hint cannot cheapen a cycle)
#   4. done present               -> done.model WINS, hint ignored, estimated:false
# (4) is the important one: the hint must never override what actually ran, or the
# model-substitution guard would be silently defeated on every priced cycle.
set -uo pipefail
ADAPTER="${1:-scripts/core/engine-usage-cost.py}"
fail=0
contains() { case "$2" in *"$3"*) echo "  PASS $1" ;; *) echo "  FAIL $1: '$3' not in '$2'"; fail=1 ;; esac; }
not_contains() { case "$2" in *"$3"*) echo "  FAIL $1: unexpected '$3'"; fail=1 ;; *) echo "  PASS $1" ;; esac; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

TOK='{"type":"tokens","input":1000,"output":500,"cache_read_input":2000000,"cache_creation_input":100000}'
printf '%s\n' "$TOK" > "$WORK/killed.ndjson"
printf '%s\n{"type":"done","model":"claude-sonnet-5"}\n' "$TOK" > "$WORK/complete.ndjson"

cost_of() { printf '%s' "$1" | python3 -c 'import json,sys; print(json.load(sys.stdin)["cost_usd"])'; }

echo "--- 1: no hint, no done event — conservative row unchanged ---"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/killed.ndjson")
contains "unknown model"      "$out" '"model": "unknown"'
contains "conservative basis" "$out" "UNKNOWN MODEL"
contains "flagged estimated"  "$out" '"estimated": true'
base_cost=$(cost_of "$out")

echo "--- 2: valid hint, no done event — real tariff, still flagged ---"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/killed.ndjson" --model-hint claude-sonnet-5)
contains "hinted model used"  "$out" '"model": "claude-sonnet-5"'
contains "basis names hint"   "$out" "requested-model HINT"
contains "never calibrated"   "$out" '"estimated": true'
hint_cost=$(cost_of "$out")
python3 -c "
import sys
base, hint = float('$base_cost'), float('$hint_cost')
ok = hint < base / 4
print(('  PASS hint removes the phantom (%.4f vs %.4f)' if ok else '  FAIL hint did not cut cost (%.4f vs %.4f)') % (hint, base))
sys.exit(0 if ok else 1)
" || fail=1

echo "--- 3: UNRECOGNISED hint — still conservative (bad hint cannot cheapen) ---"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/killed.ndjson" --model-hint totally-made-up-model)
contains "conservative retained" "$out" "UNKNOWN MODEL"
bad_cost=$(cost_of "$out")
if [ "$bad_cost" = "$base_cost" ]; then echo "  PASS priced identically to no-hint"; else echo "  FAIL $bad_cost != $base_cost"; fail=1; fi

echo "--- 4: done event present — done.model WINS, hint ignored ---"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/complete.ndjson" --model-hint claude-haiku-4-5-20251001)
contains     "actual model kept"  "$out" '"model": "claude-sonnet-5"'
not_contains "no hint marker"     "$out" "requested-model HINT"
contains     "stays calibrated"   "$out" '"estimated": false'

echo "--- 5: Sonnet 5 priced at the official 2/10 list (2026-10-11 recalibration) ---"
# 1000 in*2 + 500 out*10 + 2M read*2*0.10 + 100k write*2*2.0 = 2000+5000+400000+400000 = 0.807
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/complete.ndjson")
s5_cost=$(cost_of "$out")
if [ "$s5_cost" = "0.807" ]; then echo "  PASS sonnet-5 = 0.807"; else echo "  FAIL sonnet-5 cost $s5_cost != 0.807"; fail=1; fi
contains "basis v2" "$out" "list-price table v2"

echo "--- 6: Sonnet 5.5 — same in/out, cache READ at 0.05x (row-level multiplier) ---"
# 2000 + 5000 + 2M*2*0.05 (=200000) + 400000 = 0.607
printf '%s\n{"type":"done","model":"claude-sonnet-5-5"}\n' "$TOK" > "$WORK/s55.ndjson"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/s55.ndjson")
s55_cost=$(cost_of "$out")
contains "model kept"       "$out" '"model": "claude-sonnet-5-5"'
contains "calibrated row"   "$out" '"estimated": false'
if [ "$s55_cost" = "0.607" ]; then echo "  PASS sonnet-5-5 = 0.607"; else echo "  FAIL sonnet-5-5 cost $s55_cost != 0.607"; fail=1; fi

echo "--- 7: rows without a third element keep the uniform 0.10x read multiplier ---"
printf '%s\n{"type":"done","model":"claude-haiku-4-5"}\n' "$TOK" > "$WORK/haiku.ndjson"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/haiku.ndjson")
# 1000*1 + 500*5 + 2M*1*0.10 + 100k*1*2.0 = 1000+2500+200000+200000 = 0.4035
h_cost=$(cost_of "$out")
if [ "$h_cost" = "0.4035" ]; then echo "  PASS haiku unchanged = 0.4035"; else echo "  FAIL haiku cost $h_cost != 0.4035"; fail=1; fi

echo "--- 8: Opus 5.5 — 4/20 list, cache READ at 0.05x (2026-10-12) ---"
# 1000*4 + 500*20 + 2M*4*0.05 (=400000) + 100k*4*2.0 (=800000) = 4000+10000+400000+800000 = 1.214
printf '%s\n{"type":"done","model":"claude-opus-5-5"}\n' "$TOK" > "$WORK/o55.ndjson"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/o55.ndjson")
o55_cost=$(cost_of "$out")
contains "model kept"     "$out" '"model": "claude-opus-5-5"'
contains "calibrated row" "$out" '"estimated": false'
if [ "$o55_cost" = "1.214" ]; then echo "  PASS opus-5-5 = 1.214"; else echo "  FAIL opus-5-5 cost $o55_cost != 1.214"; fail=1; fi

echo "--- 9: Opus 5 — 5/25 list (was assumed 15/75), uniform 0.10x read ---"
# 1000*5 + 500*25 + 2M*5*0.10 (=1000000) + 100k*5*2.0 (=1000000) = 5000+12500+1000000+1000000 = 2.0175
printf '%s\n{"type":"done","model":"claude-opus-5"}\n' "$TOK" > "$WORK/o5.ndjson"
out=$(python3 "$ADAPTER" --ndjson-file "$WORK/o5.ndjson")
o5_cost=$(cost_of "$out")
if [ "$o5_cost" = "2.0175" ]; then echo "  PASS opus-5 = 2.0175"; else echo "  FAIL opus-5 cost $o5_cost != 2.0175"; fail=1; fi

echo
if [ "$fail" = "0" ]; then echo "ALL PASS"; else echo "FAILURES"; exit 1; fi
