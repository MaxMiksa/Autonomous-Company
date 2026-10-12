#!/usr/bin/env python3
"""engine-usage-cost — token usage -> notional USD at Anthropic list prices.

Why this exists (jcode migration, gate 3): `claude -p --output-format json`
reports `total_cost_usd` and the APP-263 four-gate budget ledger is fed from
it. jcode reports token counts only (`done.usage` in --ndjson), so the ledger
needs this adapter to keep the gates seeing real numbers. A budget gate that
silently reads zero is not a brake — hence the conservative-unknown design:
an unknown model is priced at the most expensive known row times a safety
factor, loudly flagged, never zero. Set STRICT=1 to hard-fail instead.

Input (choose one):
  --usage-json '<json>'   usage object (Claude API field names)
  --ndjson-file PATH      jcode --ndjson event stream. ALL `tokens` events are
                          SUMMED — measured 2026-07-31: `done.usage` carries
                          the LAST request only, so trusting it on a
                          multi-tool cycle undercounts by the whole agentic
                          loop. The `done` event is used only for the model
                          name (it records what ACTUALLY ran, including
                          jcode's silent fallback on an unknown -m).
Output: one JSON line:
  {"model":..., "cost_usd":..., "estimated":false, "basis":"..."}
Exit codes: 0 ok; 2 bad input; 3 unknown model under STRICT=1.

Verified 2026-07-31 against claude CLI's own total_cost_usd / modelUsage on
live haiku-4-5 and sonnet-5 calls (see jcode-pilot acceptance log).
"""

import argparse
import json
import os
import sys

# USD per MTok: (input, output[, cache_read_multiplier]). Cache multipliers are
# Anthropic-standard: write(5m)=1.25x input, write(1h)=2x input, read=0.1x input —
# EXCEPT where a row carries its own third element (Sonnet 5.5 reads at 0.05x).
# Keep this table SHORT and verified — an entry here is a claim checked against
# the official price list or the CLI's own accounting.
#
# Sonnet rows re-calibrated 2026-10-11 from platform.claude.com/docs/en/about-claude/pricing:
# Sonnet 5 is $2/$10 (the "introductory" price was made permanent — pricing footnote 3;
# the 3/15 row here over-counted every Sonnet cycle by 50% since 2026-07). Sonnet 5.5 is
# the same $2/$10 with cache READ at 0.05x ($0.10/M vs $0.20/M) — footnote 2 — and a
# 512-token minimum cacheable prompt (Sonnet 5: 1024). Not calibrated against a kept
# ndjson yet; first sonnet-5-5 prod cycle's done.usage is the calibration point.
PRICES = {
    "claude-sonnet-5":            (2.00, 10.00),
    "claude-sonnet-5-20250929":   (2.00, 10.00),
    "claude-sonnet-5-5":          (2.00, 10.00, 0.05),
    "claude-haiku-4-5":           (1.00, 5.00),
    "claude-haiku-4-5-20251001":  (1.00, 5.00),
    # Opus rows: official list price platform.claude.com/docs/en/about-claude/pricing,
    # 2026-10-12; Opus 5.5 cache-read 0.20/M = 0.05x; previous 15/75 was an assumption
    # (opus-4.x era list price, never calibrated). Not yet checked against a kept ndjson.
    "claude-opus-5":              (5.00, 25.00),
    "claude-opus-5-5":            (4.00, 20.00, 0.05),
    # Calibrated 2026-07-31 from litellm model_prices (canonical OpenAI-direct
    # row, azure/bedrock variants ignored). cache_read is $0.50/M = exactly
    # 0.10x input, so the uniform CACHE_R below is correct for this row too;
    # OpenAI has no cache-write surcharge and its tokens events carry
    # cache_creation_input: null -> _n() zeroes it, write multipliers never
    # engage. Validated same day against a kept ndjson run (hand-calc match).
    "gpt-5.6-sol":                (5.00, 30.00),
}
CACHE_W_5M, CACHE_W_1H, CACHE_R = 1.25, 2.00, 0.10
# Aggregate cache_creation with no TTL breakdown (jcode's shape) is priced at
# the 1h rate: measured 2026-07-31 — claude CLI writes ephemeral_1h and its
# own costUSD matches 2.0x exactly (1.25x was off by the full write volume).
# Correct for this stack AND conservative if a 5m write ever slips through.
CACHE_W_DEFAULT = CACHE_W_1H
# Unknown-model fallback: max known input/output row times this factor.
CONSERVATIVE_FACTOR = 5.0


def _n(v) -> int:
    """None-safe int. OpenAI-provider tokens events carry cache_creation_input:
    null (no cache-write concept there) — measured 2026-07-31; int(None) raises."""
    return int(v or 0)


def cost_for(model: str, u: dict) -> dict:
    inp = _n(u.get("input_tokens"))
    out = _n(u.get("output_tokens"))
    c_r = _n(u.get("cache_read_input_tokens"))
    c_w = _n(u.get("cache_creation_input_tokens"))
    # claude CLI sometimes breaks cache_creation down by TTL; honor it.
    cc = u.get("cache_creation") or {}
    w5 = _n(cc.get("ephemeral_5m_input_tokens"))
    w1 = _n(cc.get("ephemeral_1h_input_tokens"))
    if w5 or w1:
        c_w = 0  # priced via the breakdown instead

    known = model in PRICES
    cache_r = CACHE_R
    if known:
        row = PRICES[model]
        p_in, p_out = row[0], row[1]
        if len(row) > 2:
            cache_r = row[2]
        estimated = False
    else:
        if os.environ.get("STRICT") == "1":
            print(f"unknown model {model!r} and STRICT=1", file=sys.stderr)
            sys.exit(3)
        p_in = max(p[0] for p in PRICES.values()) * CONSERVATIVE_FACTOR
        p_out = max(p[1] for p in PRICES.values()) * CONSERVATIVE_FACTOR
        estimated = True

    usd = (
        inp * p_in
        + out * p_out
        + c_r * p_in * cache_r
        + c_w * p_in * CACHE_W_DEFAULT
        + w5 * p_in * CACHE_W_5M
        + w1 * p_in * CACHE_W_1H
    ) / 1_000_000
    return {
        "model": model,
        "cost_usd": round(usd, 8),
        "estimated": estimated,
        "basis": "list-price table v2"
        + ("" if known else f" (UNKNOWN MODEL — max row x{CONSERVATIVE_FACTOR})"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    # Consulted ONLY when the stream carries no `done` event — i.e. the cycle was
    # killed (timeout/OOM) before jcode could report what ran. The token counts in
    # that stream are REAL (summed `tokens` events up to the kill); the only unknown
    # is model identity, and the loop does know which model it REQUESTED. Without
    # this, such a cycle priced at the unknown-model row × the conservative factor:
    # measured 2026-08-01, one timed-out cycle booked $63.63 against a real ~$12.7
    # and filled 64% of the 5h window on its own. The result stays `estimated: true`
    # and names the hint in `basis` — a hinted price is never a calibrated one, and
    # an unrecognised hint still falls through to the conservative row.
    ap.add_argument("--model-hint", default=None)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--usage-json")
    src.add_argument("--ndjson-file")
    args = ap.parse_args()
    hinted = False

    if args.usage_json:
        if not args.model:
            print("--model is required with --usage-json", file=sys.stderr)
            return 2
        try:
            usage = json.loads(args.usage_json)
        except json.JSONDecodeError as e:
            print(f"bad usage json: {e}", file=sys.stderr)
            return 2
        model = args.model
    else:
        done = None
        totals = {"input_tokens": 0, "output_tokens": 0,
                  "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        tokens_events = 0
        try:
            with open(args.ndjson_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if ev.get("type") == "tokens":
                        tokens_events += 1
                        totals["input_tokens"] += _n(ev.get("input"))
                        totals["output_tokens"] += _n(ev.get("output"))
                        totals["cache_read_input_tokens"] += _n(ev.get("cache_read_input"))
                        totals["cache_creation_input_tokens"] += _n(ev.get("cache_creation_input"))
                    elif ev.get("type") == "done":
                        done = ev
        except OSError as e:
            print(f"cannot read ndjson: {e}", file=sys.stderr)
            return 2
        if tokens_events == 0:
            # Fall back to done.usage (single-request runs emit it too), but
            # never silently produce a zero-cost result.
            if done and isinstance(done.get("usage"), dict):
                usage = done["usage"]
            else:
                print("no tokens events and no done.usage in ndjson", file=sys.stderr)
                return 2
        else:
            usage = totals
        # The done event records what ACTUALLY ran (jcode silently falls back
        # to its default model on an unknown -m). Trust it unless overridden.
        # The hint ranks BELOW done.model on purpose: it may only stand in where
        # there is no done event at all, never override one that exists.
        model = args.model or (done or {}).get("model") or args.model_hint or "unknown"
        if not done and args.model_hint and model == args.model_hint:
            hinted = True

    result = cost_for(model, usage)
    if hinted:
        result["estimated"] = True
        result["basis"] += " (requested-model HINT — no done event; the cycle was killed)"
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
