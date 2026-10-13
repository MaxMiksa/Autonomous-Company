#!/bin/bash

set -euo pipefail

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_ROOT="$(cd "$TEST_DIR/.." && pwd)"
PROJECT_SCRIPT="$SOURCE_ROOT/scripts/core/project.sh"
GUARD_SCRIPT="$SOURCE_ROOT/scripts/core/consensus-guard.sh"
TEMP_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TEMP_ROOT"' EXIT

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_file() {
    [ -f "$1" ] || fail "expected file: $1"
}

assert_contains() {
    local file="$1" pattern="$2"
    grep -Fq -- "$pattern" "$file" || fail "expected '$pattern' in $file"
}

echo "[1/5] independent project creation, status, and explicit publish gate"
FRAMEWORK="$TEMP_ROOT/framework"
mkdir -p "$FRAMEWORK/projects" "$FRAMEWORK/scripts/core"
cp "$SOURCE_ROOT/.gitignore" "$FRAMEWORK/.gitignore"
cp "$SOURCE_ROOT/projects/registry.tsv" "$FRAMEWORK/projects/registry.tsv"
cp "$PROJECT_SCRIPT" "$FRAMEWORK/scripts/core/project.sh"
cp "$SOURCE_ROOT/scripts/core/project-context.py" "$FRAMEWORK/scripts/core/"
git -C "$FRAMEWORK" init --initial-branch=main >/dev/null
git -C "$FRAMEWORK" config user.name "Governance Test"
git -C "$FRAMEWORK" config user.email "governance-test@example.invalid"
git -C "$FRAMEWORK" add .
git -C "$FRAMEWORK" commit -m "framework baseline" >/dev/null

AUTONOMOUS_COMPANY_ROOT="$FRAMEWORK" "$PROJECT_SCRIPT" new --name test-product > "$TEMP_ROOT/new.out"
assert_file "$FRAMEWORK/projects/test-product/.git/HEAD"
[ ! -e "$FRAMEWORK/.autonomous-company.local" ] || fail "project-new changed human selection"
AUTONOMOUS_COMPANY_ROOT="$FRAMEWORK" "$PROJECT_SCRIPT" select --project test-product --confirm SELECT
assert_contains "$FRAMEWORK/.autonomous-company.local" "ACTIVE_PROJECT=projects/test-product"
[ -z "$(git -C "$FRAMEWORK/projects/test-product" remote)" ] || fail "project-new created a remote"

AUTONOMOUS_COMPANY_ROOT="$FRAMEWORK" "$PROJECT_SCRIPT" status > "$TEMP_ROOT/status.out"
assert_contains "$TEMP_ROOT/status.out" "REPOSITORY=independent-local-git"
assert_contains "$TEMP_ROOT/status.out" "ORIGIN=none"
assert_contains "$TEMP_ROOT/status.out" "FRAMEWORK_PROJECT_FILES=ignored"

framework_changes="$(git -C "$FRAMEWORK" status --porcelain)"
printf '%s\n' "$framework_changes" | grep -q 'projects/registry.tsv' || fail "registry change not visible to framework"
printf '%s\n' "$framework_changes" | grep -q 'projects/test-product' && fail "product source leaked into framework status"
printf '%s\n' "$framework_changes" | grep -q '.autonomous-company.local' && fail "local ACTIVE_PROJECT config leaked into framework status"

git -C "$FRAMEWORK/projects/test-product" config user.name "Product Test"
git -C "$FRAMEWORK/projects/test-product" config user.email "product-test@example.invalid"
git -C "$FRAMEWORK/projects/test-product" add .
git -C "$FRAMEWORK/projects/test-product" commit -m "initial product" >/dev/null

set +e
AUTONOMOUS_COMPANY_ROOT="$FRAMEWORK" "$PROJECT_SCRIPT" publish --remote-url "$TEMP_ROOT/remote.git" > "$TEMP_ROOT/publish-denied.out" 2>&1
publish_denied_status=$?
set -e
[ "$publish_denied_status" -ne 0 ] || fail "publish worked without explicit confirmation"
[ -z "$(git -C "$FRAMEWORK/projects/test-product" remote)" ] || fail "denied publish created a remote"

git init --bare "$TEMP_ROOT/remote.git" >/dev/null
AUTONOMOUS_COMPANY_ROOT="$FRAMEWORK" "$PROJECT_SCRIPT" publish --remote-url "$TEMP_ROOT/remote.git" --confirm PUBLISH > "$TEMP_ROOT/publish.out"
[ "$(git -C "$FRAMEWORK/projects/test-product" remote get-url origin)" = "$TEMP_ROOT/remote.git" ] || fail "explicit publish did not configure origin"
git --git-dir="$TEMP_ROOT/remote.git" rev-parse --verify refs/heads/main >/dev/null || fail "explicit publish did not push main"
grep -Eq '^test-product[[:space:]]+projects/test-product[[:space:]]+published[[:space:]]' "$FRAMEWORK/projects/registry.tsv" || fail "registry was not marked published"

echo "[2/5] reversible migration path preserves a tracked legacy product"
MIGRATION_FRAMEWORK="$TEMP_ROOT/migration-framework"
mkdir -p "$MIGRATION_FRAMEWORK/projects/legacy-product"
cp "$SOURCE_ROOT/.gitignore" "$MIGRATION_FRAMEWORK/.gitignore"
printf 'name\tpath\tlifecycle\tcreated_at_utc\nlegacy-product\tprojects/legacy-product\tlegacy-tracked\tunknown\n' > "$MIGRATION_FRAMEWORK/projects/registry.tsv"
printf 'legacy asset\n' > "$MIGRATION_FRAMEWORK/projects/legacy-product/app.txt"
git -C "$MIGRATION_FRAMEWORK" init --initial-branch=main >/dev/null
git -C "$MIGRATION_FRAMEWORK" config user.name "Migration Test"
git -C "$MIGRATION_FRAMEWORK" config user.email "migration-test@example.invalid"
git -C "$MIGRATION_FRAMEWORK" add .gitignore projects/registry.tsv
git -C "$MIGRATION_FRAMEWORK" add -f projects/legacy-product/app.txt
git -C "$MIGRATION_FRAMEWORK" commit -m "legacy framework asset" >/dev/null

set +e
AUTONOMOUS_COMPANY_ROOT="$MIGRATION_FRAMEWORK" "$PROJECT_SCRIPT" migrate-legacy --name legacy-product > "$TEMP_ROOT/migrate-denied.out" 2>&1
migrate_denied_status=$?
set -e
[ "$migrate_denied_status" -ne 0 ] || fail "legacy migration worked without explicit confirmation"
[ ! -e "$MIGRATION_FRAMEWORK/projects/legacy-product/.git" ] || fail "denied migration created nested Git metadata"

AUTONOMOUS_COMPANY_ROOT="$MIGRATION_FRAMEWORK" "$PROJECT_SCRIPT" migrate-legacy --name legacy-product --confirm MIGRATE > "$TEMP_ROOT/migrate.out"
assert_file "$MIGRATION_FRAMEWORK/projects/legacy-product/app.txt"
assert_file "$MIGRATION_FRAMEWORK/projects/legacy-product/.git/HEAD"
assert_file "$MIGRATION_FRAMEWORK/.autonomous-company-migrations/legacy-product/project.bundle"
git -C "$MIGRATION_FRAMEWORK/projects/legacy-product" rev-parse --verify HEAD >/dev/null || fail "migrated project has no local commit"
git -C "$MIGRATION_FRAMEWORK" diff --cached --name-status | grep -q '^D.*projects/legacy-product/app.txt' || fail "framework untracking was not staged for review"

AUTONOMOUS_COMPANY_ROOT="$MIGRATION_FRAMEWORK" "$PROJECT_SCRIPT" migrate-rollback --name legacy-product --confirm ROLLBACK > "$TEMP_ROOT/migrate-rollback.out"
assert_file "$MIGRATION_FRAMEWORK/projects/legacy-product/app.txt"
[ ! -e "$MIGRATION_FRAMEWORK/projects/legacy-product/.git" ] || fail "rollback left nested Git metadata active"
assert_file "$MIGRATION_FRAMEWORK/.autonomous-company-migrations/legacy-product/project.git/HEAD"
git -C "$MIGRATION_FRAMEWORK" ls-files --error-unmatch projects/legacy-product/app.txt >/dev/null || fail "rollback did not restore framework tracking"
git -C "$MIGRATION_FRAMEWORK" diff --quiet || fail "rollback left tracked worktree changes"
git -C "$MIGRATION_FRAMEWORK" diff --cached --quiet || fail "rollback left staged framework changes"

echo "[3/5] Human Overrides rollback and pause"
GUARD_ROOT="$TEMP_ROOT/guard-framework"
mkdir -p "$GUARD_ROOT/memories" "$GUARD_ROOT/logs"
cp "$SOURCE_ROOT/memories/consensus.template.md" "$GUARD_ROOT/memories/consensus.template.md"
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" init
sed -i 's/- (none)/- Keep billing disabled until a human approves it./' "$GUARD_ROOT/memories/consensus.md"
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" preflight 1
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" begin 1
cp "$GUARD_ROOT/memories/consensus.md" "$TEMP_ROOT/expected-consensus.md"
sed -i 's/- Keep billing disabled until a human approves it./- Enable billing immediately./' "$GUARD_ROOT/memories/consensus.md"

set +e
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" verify 1 > "$TEMP_ROOT/override.out" 2>&1
override_status=$?
set -e
[ "$override_status" -eq 42 ] || fail "override mutation did not return pause code 42"
cmp -s "$TEMP_ROOT/expected-consensus.md" "$GUARD_ROOT/memories/consensus.md" || fail "consensus was not fully restored"
assert_file "$GUARD_ROOT/.auto-loop-paused"
assert_contains "$GUARD_ROOT/.auto-loop-paused" "PAUSE_REASON=human_override_mutated"
assert_contains "$GUARD_ROOT/.auto-loop-state" "STATUS=paused"
assert_contains "$GUARD_ROOT/.auto-loop-state" "PAUSE_REASON=human_override_mutated"
assert_contains "$GUARD_ROOT/logs/auto-loop.log" "[CRITICAL] HIGH PRIORITY: Cycle changed or deleted Human Overrides"
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" close 1
rm -f "$GUARD_ROOT/.auto-loop-paused"

AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" begin 11
cp "$GUARD_ROOT/memories/consensus.md" "$TEMP_ROOT/expected-consensus-delete.md"
sed -i '/^## Human Overrides$/,/^## Priority Issues$/{ /^## Priority Issues$/!d; }' "$GUARD_ROOT/memories/consensus.md"
set +e
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" verify 11 > "$TEMP_ROOT/override-delete.out" 2>&1
override_delete_status=$?
set -e
[ "$override_delete_status" -eq 42 ] || fail "override deletion did not return pause code 42"
cmp -s "$TEMP_ROOT/expected-consensus-delete.md" "$GUARD_ROOT/memories/consensus.md" || fail "deleted override did not restore the full consensus"
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" close 11
rm -f "$GUARD_ROOT/.auto-loop-paused"

echo "[4/5] unresolved P1 blocks a fake cycle before execution"
sed -i '/^## Priority Issues$/a\- [ ] P1: legal approval is missing' "$GUARD_ROOT/memories/consensus.md"
set +e
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" preflight 2 > "$TEMP_ROOT/p1.out" 2>&1 && touch "$TEMP_ROOT/fake-engine-called"
p1_status=$?
set -e
[ "$p1_status" -eq 41 ] || fail "unresolved P1 did not return block code 41"
[ ! -e "$TEMP_ROOT/fake-engine-called" ] || fail "fake cycle executed despite unresolved P1"
assert_contains "$GUARD_ROOT/logs/auto-loop.log" "[P1_BLOCK] Unresolved P1 blocks this cycle before engine invocation"
assert_contains "$GUARD_ROOT/.auto-loop-state" "STATUS=paused"
assert_contains "$GUARD_ROOT/.auto-loop-state" "PAUSE_REASON=unresolved_p1"

echo "[5/5] successful fake cycle saves a consensus snapshot"
sed -i 's/- \[ \] P1: legal approval is missing/- [x] P1: legal approval is complete/' "$GUARD_ROOT/memories/consensus.md"
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" preflight 2
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" begin 2
sed -i 's/Not started/2026-09-02T00:00:00Z/' "$GUARD_ROOT/memories/consensus.md"
AUTONOMOUS_COMPANY_ROOT="$GUARD_ROOT" "$GUARD_SCRIPT" finish 2 > "$TEMP_ROOT/finish.out"
snapshot_count="$(find "$GUARD_ROOT/memories/snapshots" -type f -name 'consensus-cycle-0002-*.md' | wc -l | tr -d ' ')"
[ "$snapshot_count" -eq 1 ] || fail "expected one successful consensus snapshot"
snapshot_file="$(find "$GUARD_ROOT/memories/snapshots" -type f -name 'consensus-cycle-0002-*.md')"
cmp -s "$GUARD_ROOT/memories/consensus.md" "$snapshot_file" || fail "snapshot does not match successful consensus"

echo "PASS: project governance and consensus guard"
