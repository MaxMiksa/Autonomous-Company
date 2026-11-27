"""Run each published example's core checks in its own working directory."""

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
NODE_TESTS = {
    "chart-proof": ("tests/core.test.cjs",),
    "coi-chase-desk": ("tests/smoke.test.js",),
    "crm-migration-proof": ("tests/engine.test.js",),
    "crossed-island-experiment": ("tests/engine.test.js",),
    "cuecheck": ("tests/core.test.js",),
    "dual-flavor-table": ("tests/engine.test.js",),
    "family-memory": ("tests/core.test.js", "tests/recovery.test.js"),
    "participation-recovery": ("tests/core.test.js", "tests/recovery.test.js"),
    "rest-rhythm": ("tests/core.test.js",),
    "reversible-room": ("tests/core.test.js",),
    "scopefence": ("tests/scopefence-core.test.mjs",),
    "spec-evidence": ("tests/core.test.js",),
    "tabledelta": ("tests/core.test.js",),
    "tujiandan": ("tests/core.test.js", "tests/i18n.test.js"),
}
PYTHON_TESTS = {
    "disclosure-qa-spike": (
        "tests.test_workflow.CoreFlowTests", "tests.test_workflow.FailureRecoveryTests",
        "tests.test_workflow.HttpWorkflowTests",
    ),
    "field-return-audit": ("tests.test_audit", "tests.test_server"),
    "ifc-source-preflight": ("tests.test_preflight", "tests.test_server"),
}
# These products have no separate core suite. Their real entrypoints are covered
# by tests/browser/showcase.spec.js; retain this explicit inventory for new apps.
BROWSER_ONLY = {"family-art-show", "tactile-preflight"}
SYNTAX = {}
# These suites also have required product jobs. Defer only when routing selected
# those jobs; an ordinary change to another example still checks every suite.
PRODUCT_JOBS = {"tabledelta", "cuecheck"}


def commands():
    result = {name: ["node", "--test", *tests] for name, tests in NODE_TESTS.items()}
    result.update({name: [sys.executable, "-m", "unittest", "-v", *tests]
                   for name, tests in PYTHON_TESTS.items()})
    result.update({name: ["node", "--check", *files] for name, files in SYNTAX.items()})
    return result


def validate_inventory(root=ROOT):
    actual = {path.name for path in (root / "examples").iterdir() if path.is_dir()}
    expected = set(commands()) | BROWSER_ONLY
    if actual != expected:
        raise ValueError(f"Example CI inventory differs: unregistered={sorted(actual - expected)}, "
                         f"missing={sorted(expected - actual)}")
    for name, files in {**NODE_TESTS, **SYNTAX}.items():
        for filename in files:
            if not (root / "examples" / name / filename).is_file():
                raise ValueError(f"Example CI check is missing: {name}/{filename}")
    for name, tests in PYTHON_TESTS.items():
        for test in tests:
            # Entries may name unittest classes as well as modules.
            filename = "/".join(test.split(".")[:2]) + ".py"
            if not (root / "examples" / name / filename).is_file():
                raise ValueError(f"Example CI check is missing: {name}/{filename}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--defer", nargs="*", choices=sorted(PRODUCT_JOBS), default=[],
                        help="suites selected for their required product jobs")
    args = parser.parse_args(argv)
    validate_inventory()
    failed = []
    for name, command in sorted(commands().items()):
        if name in args.defer:
            print(f"Example core checks: {name} deferred to its required product job", flush=True)
            continue
        print(f"Example core checks: {name}", flush=True)
        try:
            result = subprocess.run(command, cwd=ROOT / "examples" / name, check=False)
            code = result.returncode
        except OSError as exc:
            print(f"Could not launch {name}: {exc}", file=sys.stderr, flush=True)
            code = 127
        if code:
            failed.append(name)
    print(f"Core/syntax groups: {len(commands()) - len(set(args.defer))}; failed: {failed}; "
          f"deferred product jobs: {', '.join(sorted(set(args.defer))) or 'none'}; "
          f"browser-only entries: {', '.join(sorted(BROWSER_ONLY))}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
