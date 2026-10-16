#!/usr/bin/env python3
"""role-checklist.py — role files as harness-injected checklists (plan v4.1 §3.4, "Path B").

The jcode loop does not load `.claude/agents/*` as agents and its skill tool does not see
`.claude/skills/` (A0.2, 2026-10-16). Roles therefore reach a cycle only as text the
harness injects: for a work card's gate, the `## Gate Checklist` of each active role mapped
to that gate, capped at a byte budget. The reviewer scores the same items against evidence.

Subcommands:
  check [--agents-dir D]                 validate every role file; exit 0 ok, 2 invalid
  render --gate GN [--roles a,b]         print the checklist block for a gate (or an explicit
         [--card card.json] [--budget N] role list); a card supplies gate + optional roles.
                                         Fail-safe: any error prints nothing and exits 0, so
                                         a broken role file can never break prompt assembly.
  list [--agents-dir D]                  role, status, gates, priority — one line each
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / ".claude" / "agents"
SECTIONS = [
    "Identity & Memory", "Core Mission", "Critical Rules", "Deliverables", "Workflow",
    "Communication Style", "Learning & Memory", "Success Metrics", "Advanced Capabilities",
    "Gate Checklist", "Loop Metadata",
]
META_KEYS = {"status", "department", "gates", "checklist_priority", "docs_dir"}
DEPARTMENTS = {"Management", "Finance", "Legal & Compliance", "Operations", "Quality",
               "Technology", "Research", "Dormant"}
GATES = [f"G{i}" for i in range(8)]
CHECKLIST_MAX_BYTES = 280
FILE_MAX_BYTES = 7000
DEFAULT_BUDGET = 1024
# Instructions to the company are English only (operator K-2, 2026-10-16): any non-ASCII
# character outside a few typographic marks is refused — that covers CJK and Turkish letters.
ALLOWED_NON_ASCII = set("—–§≤≥→’“”×")


def parse(path):
    """Return (frontmatter, {section: body}, section order, raw text). Raises ValueError."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("missing YAML frontmatter")
    front = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if sep:
            front[k.strip()] = v.strip().strip('"')
    body = text[m.end():]
    order, sections, cur = [], {}, None
    for line in body.splitlines():
        h = re.match(r"^## (.+?)\s*$", line)
        if h:
            cur = h.group(1)
            order.append(cur)
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    return front, {k: "\n".join(v).strip() for k, v in sections.items()}, order, text


def bullets(block):
    return [ln[2:].strip() for ln in block.splitlines() if ln.startswith("- ")]


def metadata(block):
    meta = {}
    for item in bullets(block):
        k, sep, v = item.partition(":")
        if sep:
            meta[k.strip()] = v.strip()
    gates = [g.strip() for g in meta.get("gates", "").split(",") if g.strip() and g.strip() != "none"]
    meta["gates"] = gates
    return meta


def validate(path):
    """Return a list of errors for one role file (empty = valid)."""
    e = []
    try:
        front, sec, order, text = parse(path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return [f"{path.name}: {exc}"]
    n = path.name
    if front.get("name") != path.stem:
        e.append(f"{n}: frontmatter name must equal file stem '{path.stem}'")
    if not front.get("description"):
        e.append(f"{n}: frontmatter description required")
    if front.get("model") != "inherit":
        e.append(f"{n}: frontmatter model must be 'inherit'")
    if order != SECTIONS:
        e.append(f"{n}: H2 sections must be exactly, in order: {SECTIONS} (got {order})")
    bad = sorted({c for c in text if ord(c) > 127 and c not in ALLOWED_NON_ASCII})
    if bad:
        e.append(f"{n}: English-only — disallowed characters {''.join(bad)!r}")
    if len(text.encode("utf-8")) > FILE_MAX_BYTES:
        e.append(f"{n}: file over {FILE_MAX_BYTES} bytes")
    meta = metadata(sec.get("Loop Metadata", ""))
    unknown = set(meta) - META_KEYS
    missing = META_KEYS - set(meta)
    if unknown or missing:
        e.append(f"{n}: Loop Metadata keys must be {sorted(META_KEYS)} (unknown {sorted(unknown)}, missing {sorted(missing)})")
    status = meta.get("status")
    if status not in ("active", "dormant"):
        e.append(f"{n}: status must be active|dormant")
    if meta.get("department") not in DEPARTMENTS:
        e.append(f"{n}: department must be one of {sorted(DEPARTMENTS)}")
    if any(g not in GATES for g in meta["gates"]):
        e.append(f"{n}: gates must be a comma list from G0..G7 or 'none'")
    if not re.fullmatch(r"[1-9]", meta.get("checklist_priority", "")):
        e.append(f"{n}: checklist_priority must be 1..9")
    if not re.fullmatch(r"docs/[a-z0-9-]+/", meta.get("docs_dir", "")):
        e.append(f"{n}: docs_dir must look like docs/<dir>/")
    items = bullets(sec.get("Gate Checklist", ""))
    if status == "dormant":
        if meta["gates"]:
            e.append(f"{n}: a dormant role maps to no gate (S2: dormant roles leave cycle selection)")
        if not front.get("description", "").startswith("DORMANT"):
            e.append(f"{n}: a dormant role's description starts with 'DORMANT'")
    elif status == "active":
        if not 2 <= len(items) <= 4:
            e.append(f"{n}: Gate Checklist needs 2-4 bullets")
        size = len("\n".join(f"- {i}" for i in items).encode("utf-8"))
        if size > CHECKLIST_MAX_BYTES:
            e.append(f"{n}: Gate Checklist is {size} bytes (max {CHECKLIST_MAX_BYTES})")
        if len(bullets(sec.get("Success Metrics", ""))) < 2:
            e.append(f"{n}: Success Metrics needs at least 2 measurable bullets")
    return e


def load_roles(agents_dir):
    roles = {}
    for path in sorted(agents_dir.glob("*.md")):
        _front, sec, _order, _text = parse(path)
        meta = metadata(sec.get("Loop Metadata", ""))
        roles[path.stem] = {
            "status": meta.get("status"),
            "gates": meta["gates"],
            "priority": int(meta.get("checklist_priority", "9")),
            "items": bullets(sec.get("Gate Checklist", "")),
        }
    return roles


def render(roles, gate, explicit=None, budget=DEFAULT_BUDGET):
    """Checklist block for a gate. Active roles only; priority, then name; byte-capped."""
    active = {k: v for k, v in roles.items() if v["status"] == "active"}
    if explicit:
        chosen = [r for r in explicit if r in active]
    else:
        chosen = [r for r in active if gate in active[r]["gates"]]
    chosen.sort(key=lambda r: (active[r]["priority"], r))
    head = (f"Role checklists for this card (gate {gate}). Each item must be met by an evidence "
            f"entry on the card; the independent reviewer scores them item by item.")
    def size(lines):
        return len("\n".join(lines).encode("utf-8"))

    def tail(names):
        return f"(omitted for size: {', '.join(names)} — read their files under .claude/agents/)"

    parts, omitted = [], []
    for r in chosen:
        part = "\n".join([f"[{r}]"] + [f"- {i}" for i in active[r]["items"]])
        if size([head] + parts + [part]) <= budget:
            parts.append(part)
        else:
            omitted.append(r)
    # An omission is never silent: give up included roles (lowest priority first, never
    # the first one) until the omission line fits.
    while omitted and len(parts) > 1 and size([head] + parts + [tail(omitted)]) > budget:
        omitted.insert(0, chosen[len(parts) - 1])
        parts.pop()
    out = [head] + parts + ([tail(omitted)] if omitted else [])
    return "\n".join(out) if parts else ""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "list", "render"):
        p = sub.add_parser(name)
        p.add_argument("--agents-dir", type=Path, default=AGENTS_DIR)
    r = sub.choices["render"]
    r.add_argument("--gate")
    r.add_argument("--roles", default="")
    r.add_argument("--card", type=Path)
    r.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    a = ap.parse_args(argv)

    if a.cmd == "check":
        files = sorted(a.agents_dir.glob("*.md"))
        errors = [err for f in files for err in validate(f)] if files else ["no role files found"]
        for err in errors:
            print(err)
        print(f"role-checklist check: {len(files)} files, {len(errors)} errors")
        return 2 if errors else 0
    if a.cmd == "list":
        for name, v in load_roles(a.agents_dir).items():
            print(f"{name}\t{v['status']}\t{','.join(v['gates']) or 'none'}\tp{v['priority']}")
        return 0
    try:  # render: fail-safe — empty output, exit 0
        gate, explicit = a.gate, [x for x in a.roles.split(",") if x]
        if a.card:
            card = json.loads(a.card.read_text(encoding="utf-8"))
            gate = card.get("gate", gate)
            explicit = explicit or [x for x in card.get("roles", []) if isinstance(x, str)]
        if gate not in GATES:
            return 0
        block = render(load_roles(a.agents_dir), gate, explicit, a.budget)
        if block:
            print(block)
    except Exception:  # noqa: BLE001 — injection must never break the cycle prompt
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
