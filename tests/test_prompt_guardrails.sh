#!/usr/bin/env bash
# PROMPT.md invariants after the 2026-10 shrink (36,852 B -> <= 20,480 B):
#   (a) every REQUIRED_PROMPT_GUARDRAILS string in scripts/core/auto-loop.sh is present
#       byte-identically in PROMPT.md (the loop refuses to boot otherwise);
#   (b) PROMPT.md stays at or under the 20,480-byte budget;
#   (c) legacy (tender-era) vocabulary matches at most twice;
#   (d) the verbatim archive of the removed passages exists and is non-empty.
#
#   bash tests/test_prompt_guardrails.sh [PROMPT.md] [scripts/core/auto-loop.sh]
set -uo pipefail
PROMPT="${1:-PROMPT.md}"
LOOP="${2:-scripts/core/auto-loop.sh}"
ARCHIVE="docs/tender-archive/prompt-sections-2026-10.md"
MAX_BYTES=20480
LEGACY_RE='tender|discovery|WTP|candidate-registry|EKAP|GLOBAL_SAFETY'
LEGACY_MAX=2
fail=0
check() { if [ "$2" = "$3" ]; then echo "  PASS $1"; else echo "  FAIL $1: expected '$3' got '$2'"; fail=1; fi; }

echo "== test_prompt_guardrails =="

# (a) parse the bash array out of auto-loop.sh: quoted strings between the opening
# line and the closing paren, comments skipped.
n=0
while IFS= read -r s; do
  [ -n "$s" ] || continue
  n=$((n+1))
  if grep -qF -- "$s" "$PROMPT"; then present=yes; else present=no; fi
  check "guardrail present: $s" "$present" "yes"
done < <(awk '/^REQUIRED_PROMPT_GUARDRAILS=\(/{f=1;next} f&&/^\)/{exit} f&&/^[[:space:]]*"/{sub(/^[[:space:]]*"/,"");sub(/"[[:space:]]*$/,"");print}' "$LOOP")
check "guardrail list parsed (6 entries)" "$n" "6"

# (b) size budget
bytes=$(wc -c < "$PROMPT" | tr -d ' ')
if [ "$bytes" -le "$MAX_BYTES" ]; then ok=yes; else ok=no; fi
check "PROMPT.md size $bytes B <= $MAX_BYTES B" "$ok" "yes"

# (c) legacy vocabulary count (case-insensitive, every occurrence)
legacy=$(grep -oiE "$LEGACY_RE" "$PROMPT" | wc -l | tr -d ' ')
if [ "$legacy" -le "$LEGACY_MAX" ]; then ok=yes; else ok=no; fi
check "legacy vocabulary hits $legacy <= $LEGACY_MAX" "$ok" "yes"

# (d) archive exists and is non-empty
if [ -s "$ARCHIVE" ]; then ok=yes; else ok=no; fi
check "archive $ARCHIVE exists and is non-empty" "$ok" "yes"

if [ "$fail" -eq 0 ]; then echo "ALL PASS"; else echo "SOME FAILED"; exit 1; fi
