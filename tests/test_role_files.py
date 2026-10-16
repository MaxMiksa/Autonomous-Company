#!/usr/bin/env python3
"""Tests for the role files (.claude/agents/*) and scripts/ops/role-checklist.py.

Run: python3 tests/test_role_files.py   (no pytest dependency)
Covers: every real role file passes the standard; the roster matches plan v4.1 B5
(S2 dormant set, S3 new roles); render picks, orders, caps and fails safe.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "ops" / "role-checklist.py"
AGENTS = REPO / ".claude" / "agents"
spec = importlib.util.spec_from_file_location("role_checklist", SCRIPT)
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

_failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        _failures.append(name)


ACTIVE = {
    "ceo-bezos", "chief-of-staff", "cfo-campbell", "reconciliation-controller",
    "compliance-officer", "kvkk-dpo", "operations-pg", "interaction-cooper",
    "critic-munger", "qa-bach", "cto-vogels", "fullstack-dhh", "devops-hightower",
    "security-architect", "research-thompson",
}
DORMANT = {"marketing-godin", "sales-ross", "ui-duarte", "product-norman"}


def role_file(name, status="active", gates="G2", prio="2", items=None, extra=""):
    items = items if items is not None else ["Item one is evidenced.", "Item two is evidenced."]
    desc = ("DORMANT — " if status == "dormant" else "") + "Use for tests."
    body = "\n\n".join(
        f"## {s}\n- {s} line.\n- {s} second line." for s in rc.SECTIONS[:9]
    )
    checklist = "\n".join(f"- {i}" for i in items)
    return (f"---\nname: {name}\ndescription: \"{desc}\"\nmodel: inherit\n---\n\n# T\n{extra}\n{body}\n\n"
            f"## Gate Checklist\n{checklist}\n\n## Loop Metadata\n- status: {status}\n- department: Quality\n"
            f"- gates: {gates}\n- checklist_priority: {prio}\n- docs_dir: docs/test/\n")


def tmp_agents(files):
    d = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (d / f"{name}.md").write_text(text, encoding="utf-8")
    return d


# --- the real roster -------------------------------------------------------------------
errors = [e for f in sorted(AGENTS.glob("*.md")) for e in rc.validate(f)]
for e in errors:
    print("   ", e)
check("every real role file passes the standard", not errors)
roles = rc.load_roles(AGENTS)
check("roster = 15 active + 4 dormant (S2/S3)",
      {k for k, v in roles.items() if v["status"] == "active"} == ACTIVE
      and {k for k, v in roles.items() if v["status"] == "dormant"} == DORMANT)
check("critic-munger maps to every gate", roles.get("critic-munger", {}).get("gates") == rc.GATES)
for g in rc.GATES:
    owners = [k for k, v in roles.items() if v["status"] == "active" and g in v["gates"] and k != "critic-munger"]
    check(f"{g} has at least one owner besides critic-munger", bool(owners))
for g in rc.GATES:
    block = rc.render(roles, g)
    check(f"{g} render ≤ budget and starts with critic-munger",
          0 < len(block.encode()) <= rc.DEFAULT_BUDGET and block.splitlines()[1] == "[critic-munger]")
    mapped = {k for k, v in roles.items() if v["status"] == "active" and g in v["gates"]}
    named = {r for r in mapped if f"[{r}]" in block or r in block.splitlines()[-1]}
    check(f"{g} render names every mapped role (included or listed as omitted)", named == mapped)
proc = subprocess.run([sys.executable, str(SCRIPT), "check"], capture_output=True, text=True)
check("CLI check exits 0 on the real roster", proc.returncode == 0)

# --- validator negatives ---------------------------------------------------------------
d = tmp_agents({"x-role": role_file("x-role")})
check("synthetic valid file passes", rc.validate(d / "x-role.md") == [])
bad = {
    "cjk": role_file("cjk", extra="Note 公司\n"),
    "turkish": role_file("turkish", extra="Note şart\n"),
    "dormant-gated": role_file("dormant-gated", status="dormant", gates="G1"),
    "long-list": role_file("long-list", items=["x" * 150, "y" * 150]),
    "one-item": role_file("one-item", items=["only one"]),
    "bad-gate": role_file("bad-gate", gates="G9"),
    "bad-prio": role_file("bad-prio", prio="0"),
}
d = tmp_agents(bad)
for name in bad:
    check(f"validator rejects {name}", rc.validate(d / f"{name}.md") != [])
d = tmp_agents({"wrongname": role_file("other-name")})
check("validator rejects name != stem", rc.validate(d / "wrongname.md") != [])
d = tmp_agents({"order": role_file("order").replace("## Core Mission", "## Mission")})
check("validator rejects a renamed section", rc.validate(d / "order.md") != [])

# --- render ----------------------------------------------------------------------------
d = tmp_agents({
    "a-first": role_file("a-first", gates="G2", prio="1"),
    "b-second": role_file("b-second", gates="G2", prio="2"),
    "c-other-gate": role_file("c-other-gate", gates="G4", prio="1"),
    "d-dormant": role_file("d-dormant", status="dormant", gates="none"),
})
r = rc.load_roles(d)
out = rc.render(r, "G2")
check("render picks gate roles in priority order", out.index("[a-first]") < out.index("[b-second]"))
check("render skips other gates and dormant roles", "c-other-gate" not in out and "d-dormant" not in out)
out = rc.render(r, "G2", explicit=["c-other-gate", "d-dormant"])
check("explicit roles override the gate map, dormant still excluded",
      "[c-other-gate]" in out and "d-dormant" not in out)
small = rc.render(r, "G2", budget=len(rc.render(r, "G2", explicit=["a-first"]).encode()) + 5)
check("budget drops the lowest-priority role", "[a-first]" in small and "[b-second]" not in small)
check("render of an unmapped gate is empty", rc.render(r, "G7") == "")

card = Path(tempfile.mkdtemp()) / "card.json"
card.write_text(json.dumps({"gate": "G4"}), encoding="utf-8")
proc = subprocess.run([sys.executable, str(SCRIPT), "render", "--agents-dir", str(d), "--card", str(card)],
                      capture_output=True, text=True)
check("CLI render --card uses the card's gate", proc.returncode == 0 and "[c-other-gate]" in proc.stdout)
broken = tmp_agents({"broken": "no frontmatter at all"})
proc = subprocess.run([sys.executable, str(SCRIPT), "render", "--agents-dir", str(broken), "--gate", "G2"],
                      capture_output=True, text=True)
check("CLI render fails safe (exit 0, empty) on a broken role file", proc.returncode == 0 and proc.stdout == "")
proc = subprocess.run([sys.executable, str(SCRIPT), "check", "--agents-dir", str(broken)],
                      capture_output=True, text=True)
check("CLI check exits 2 on a broken role file", proc.returncode == 2)

print(f"\n{len(_failures)} failure(s)")
sys.exit(1 if _failures else 0)
