// Fast semantic checks for the actual journal helpers. Browser tests exercise
// the real DOM, HTTP routes, controls, escaping and language persistence.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const dashboard = path.resolve(__dirname, "../dashboard");
const html = fs.readFileSync(path.join(dashboard, "index.html"), "utf8");
const app = fs.readFileSync(path.join(dashboard, "app.js"), "utf8");
const i18n = fs.readFileSync(path.join(dashboard, "i18n.js"), "utf8");

function registerJournal(context) {
  vm.runInContext(fs.readFileSync(path.join(dashboard, "projection.js"), "utf8"), context);
  context.URL = URL;
  context.location ||= { pathname: '/products/entry-a' };
  context.location.origin = 'http://127.0.0.1:8843';
  context.document.documentElement = { lang: 'en' };
  context.window.DashboardNavigation = { register(_kind, mount) {
    mount({ document: context.document, ui: context.window.DashboardUI ||= {}, active: true,
      url: `http://127.0.0.1:8843${context.location?.pathname || '/products/entry-a'}`,
      request: () => ({ valid: () => true, done() {} }) });
  } };
}

function helpers() {
  const fields = new Map(["usagePeriod", "usageDate", "usageDateLabel", "usageRange"].map((id) => [id, {}]));
  const context = vm.createContext({ window: {}, document: {
    getElementById: (id) => { assert.ok(fields.has(id), `Unexpected DOM dependency: ${id}`); return fields.get(id); },
  } });
  vm.runInContext(fs.readFileSync(path.join(dashboard, "icons.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "projection.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "date-time.js"), "utf8"), context);
  registerJournal(context);
  vm.runInContext(i18n, context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "date-time.js"), "utf8"), context);
  // Expose existing closures before event wiring. There is no simulated DOM,
  // copied application logic, network request or production testing hook.
  const binding = app.indexOf("\n  document.querySelectorAll('[data-tab]').forEach");
  assert.ok(binding > 0, "Journal event wiring must follow its helper declarations");
  vm.runInContext(app.slice(0, binding) + "\n globalThis.journal = { state, message, aggregate, usageGroups, duration, cycleTitle, statusLabel, formatTime, fullTime, filterUsage, reportRows, liveDuration, checkCounts, checkPresentation, progressState, latestCycle, presentCycle, historyGroups, paddedCycleNumber, unavailableArtifact, mediaURL, mediaRetryError, iconPublicationWarning, publishedRefinement, readableLog, installCycleComponents, projection };\n});", context);
  context.journal.state.language = "en";
  return { ...context.journal, messages: context.window.JOURNAL_MESSAGES, vocabulary: context.window.DashboardStatus, fields };
}

test("both languages cover rendered keys and preserve interpolation fields", () => {
  const { messages } = helpers();
  assert.deepEqual(Object.keys(messages.en).sort(), Object.keys(messages["zh-CN"]).sort());
  const placeholders = (value) => [...value.matchAll(/\{([a-zA-Z]+)\}/g)].map((match) => match[1]).sort();
  for (const key of Object.keys(messages.en)) {
    assert.equal(typeof messages.en[key], "string");
    assert.ok(messages.en[key] && messages["zh-CN"][key], `Empty translation: ${key}`);
    assert.deepEqual(placeholders(messages.en[key]), placeholders(messages["zh-CN"][key]), key);
  }
  const keys = [...html.matchAll(/data-i18n="([^"]+)"/g), ...app.matchAll(/message\('([^']+)'/g)];
  for (const [, key] of keys) assert.ok(messages.en[key], `Missing rendered translation: ${key}`);
});

test('usage separates different engines and unknown model identities', () => {
  const { usageGroups, formatTime, fullTime } = helpers();
  const cycles = [{id: 'a', engine: 'codex', model: 'm1'}, {id: 'b', engine: 'codex', model: 'm1'}, {id: 'c', engine: 'other', model: 'm1'}, {id: 'd', engine: 'codex', model: 'unknown'}, {id: 'e', engine: 'codex', model: 'unknown'}];
  const groups = usageGroups(cycles);
  assert.deepEqual(Array.from(groups, group => group.cycles.length), [2, 1, 1, 1]);
  assert.match(formatTime('2020-01-01T12:00:00Z', true), /2020/);
  assert.match(fullTime('2020-01-01T12:00:00Z'), /2020/);
  assert.equal(fullTime('2020-01-01T12:00:00Z'), formatTime('2020-01-01T12:00:00Z', true));
  assert.match(fullTime('2020-01-01T12:00:00Z'), /^2020-01-01 \d{2}:\d{2}$/);
});

test('rejected optional report facts preserve only the same attempt cache', () => {
  const { installCycleComponents } = helpers();
  const cycle = attempt => ({ id: 'cycle', activeAttemptId: attempt, workReport: { title: 'Rejected observation' },
    partitions: { report: { status: 'unavailable', revision: null, errorCode: 'STALE_OBSERVATION' } } });
  const previous = { cycles: [{ id: 'cycle', activeAttemptId: 'first', workReport: { title: 'Known report' },
    partitions: { report: { revision: 3, asOf: '2026-10-22T01:00:00Z' } } }] };
  const same = { cycles: [cycle('first')] }; installCycleComponents(same, previous);
  assert.equal(same.cycles[0].workReport.title, 'Known report');
  assert.equal(same.cycles[0].partitions.report.freshness, 'stale');
  const changed = { cycles: [cycle('second')] }; installCycleComponents(changed, previous);
  assert.equal(changed.cycles[0].workReport, undefined);
  assert.equal(changed.cycles[0].partitions.report.freshness, 'unknown');
});

test('check updates do not change the facts of the independently versioned documents', () => {
  const { installCycleComponents, projection } = helpers();
  const snapshot = (status, revision) => ({ projectionVersion: 2, centerId: 'center', entryId: 'entry', sourceId: 'source',
    sourceBindingVersion: 1, projectionEpoch: 'epoch', snapshotRevision: 1, currentCycleId: 'cycle',
    cycles: [{ id: 'cycle', activeAttemptId: 'attempt', artifacts: [{ kind: 'document', id: 'doc' }, { kind: 'check', status }],
      checks: [{ kind: 'check', status }], partitions: {
        documents: { status: 'available', revision: 1 }, checks: { status: 'available', revision },
        report: { errorCode: 'NOT_REQUESTED' }, events: { errorCode: 'NOT_REQUESTED' } } }] });
  const first = snapshot('running', 1); projection.core(first); installCycleComponents(first);
  const second = snapshot('completed', 2); projection.core(second); installCycleComponents(second, first);
  assert.equal(second.cycles[0].partitions.documents.status, 'available');
  assert.equal(second.cycles[0].partitions.documents.revision, 1);
  assert.equal(second.cycles[0].artifacts.length, 1);
  assert.equal(second.cycles[0].checks[0].status, 'completed');
});

test("media links must belong to the selected center entry", () => {
  const { state, mediaURL } = helpers();
  state.data = { sourceId: 'source-a' };
  const url = `/api/center/v1/entries/entry-a/resources/media-${'b'.repeat(64)}.png?sourceId=source-a`;
  assert.equal(mediaURL(url), url);
  for (const value of [url.replace('entry-a', 'entry-b'), 'https://example.com/image.png', 'javascript:alert(1)', url.replace('/media-', '/../media-')]) assert.equal(mediaURL(value), null);
  assert.equal(mediaURL(url.replace('source-a', 'source-b')), null);
  state.data = { projectionVersion: 2, sourceId: 'source-a', sourceBindingVersion: 2, projectionEpoch: 'epoch' };
  const bound = url + '&projectionVersion=2&sourceBindingVersion=2&projectionEpoch=epoch';
  assert.equal(mediaURL(bound), bound);
  assert.equal(mediaURL(bound.replace('sourceBindingVersion=2', 'sourceBindingVersion=1')), null);
  assert.equal(mediaURL(bound.replace('projectionEpoch=epoch', 'projectionEpoch=old')), null);
});

test("published refinements require a matching read-only display language", () => {
  const { state, publishedRefinement } = helpers();
  const refinement = {language: 'en', source: 'examples/example'};
  const media = {publishedRefinement: refinement};
  state.data = {readOnly: true};
  assert.equal(publishedRefinement(media), refinement);
  state.language = 'zh-CN';
  assert.equal(publishedRefinement(media), null);
  state.language = 'en'; state.data.readOnly = false;
  assert.equal(publishedRefinement(media), null);
});

test("unconfirmed starts never become completed cycles", () => {
  const { cycleTitle, progressState, messages } = helpers();
  assert.equal(cycleTitle({status: 'startup_unconfirmed'}), messages.en.startup_unconfirmed);
  assert.equal(progressState('startup_unconfirmed'), 'unknown');
  assert.equal(progressState('not_started'), 'pending');
});

test('Harness task titles and recovery timing keep report and outcome semantics separate', () => {
  const { state, cycleTitle, progressState, liveDuration, presentCycle, messages } = helpers();
  const cycle = { id: 'cycle', harnessVersion: 2, objective: 'Compare demand evidence', status: 'closing', active: false,
    time: { reliability: 'reliable', executionSeconds: 25, recoverySeconds: 4, totalSeconds: 35 } };
  assert.equal(cycleTitle(cycle), 'Task: Compare demand evidence');
  assert.equal(progressState('closing'), 'running');
  assert.equal(progressState('handoff'), 'paused');
  state.receivedAt = 0; state.statusFailed = false; state.data = { runtime: { processState: 'stopped', currentCycleId: 'cycle' } };
  assert.equal(liveDuration(cycle, 10000), 'Execution 25s · Recovery 4s · Total 35s');
  assert.equal(liveDuration({ ...cycle, time: { reliability: 'unknown' } }, 10000), messages.en.durationUnknown);
  const executing = { ...cycle, status: 'running', activeAttemptId: 'attempt', protocolState: 'executing' };
  const unconfirmed = presentCycle(executing);
  assert.equal(unconfirmed.status, 'unknown'); assert.equal(unconfirmed.protocolState, 'executing');
  assert.equal(liveDuration(unconfirmed, 10000), messages.en.elapsedUnconfirmed);
  assert.equal(presentCycle({ ...executing, status: 'validating' }).status, 'validating');
  state.data.runtime = { active: true, currentCycleId: 'cycle', processState: 'running' };
  assert.equal(presentCycle(executing).status, 'running');
});

test("media retry errors expire after a new success or product change", () => {
  const { state, mediaRetryError } = helpers();
  state.mediaError = {productId: 'a', previousSuccess: 'old'};
  assert.equal(mediaRetryError({productId: 'a', screenshot: {state: 'failed'}}), true);
  assert.equal(mediaRetryError({productId: 'a', screenshot: {state: 'success', latestSuccess: {capturedAt: 'new'}}}), false);
  assert.equal(state.mediaError, null);
  state.mediaError = {productId: 'a', previousSuccess: null};
  assert.equal(mediaRetryError({productId: 'b', screenshot: {state: 'failed'}}), false);
});

test("canonical icon publication failures stay visible independently of source", () => {
  const { iconPublicationWarning } = helpers();
  assert.equal(iconPublicationWarning({source: 'default', publicationStatus: 'published'}), null);
  assert.equal(iconPublicationWarning({source: 'product', publicationStatus: 'existing_valid'}), null);
  assert.equal(iconPublicationWarning({source: 'product', publicationStatus: 'conflict'}), 'iconPublicationConflict');
  assert.equal(iconPublicationWarning({source: 'default', publicationStatus: 'failed'}), 'iconPublicationFailed');
  for (const publicationStatus of ['stale', 'unavailable']) assert.equal(iconPublicationWarning({source: 'product', publicationStatus}), 'iconPublicationChanged');
  assert.equal(iconPublicationWarning({reference: {state: 'preserved'}}), 'iconReferencePreserved');
  for (const state of ['missing', 'unsupported', 'unconfirmed', 'conflict', 'failed']) assert.equal(iconPublicationWarning({reference: {state}}), 'iconReferenceUnconfirmed');
  for (const state of ['inserted', 'linked', 'not_applicable']) assert.equal(iconPublicationWarning({reference: {state}}), null);
});

test("usage totals keep unknown values and coverage separate from measured zero", () => {
  const { aggregate } = helpers();
  const totals = aggregate([
    { usage: { inputTokens: 80, outputTokens: 20, totalTokens: 100 } },
    { usage: { inputTokens: null, outputTokens: null, totalTokens: null } },
    { usage: { inputTokens: 0, outputTokens: 0, totalTokens: 0 } },
  ]);
  assert.equal(totals.totalTokens, 100);
  assert.equal(totals.known, 2);
  assert.equal(totals.count, 3);
  assert.equal(totals.partial, true);
  const unknown = aggregate([{ usage: {} }, { usage: { totalTokens: -1 } }]);
  assert.equal(unknown.totalTokens, null);
  assert.equal(unknown.known, 0);
  assert.equal(aggregate([{ usage: { totalTokens: 10, status: "partial" } }]).partial, true);
  assert.equal(aggregate([]).totalTokens, null);
});

test("cycle summaries distinguish active, failed and unknown work without inventing reports", () => {
  const { cycleTitle, messages } = helpers();
  assert.equal(cycleTitle({ status: "running", active: true }), messages.en.runningSummary);
  assert.equal(cycleTitle({ status: "failed" }), messages.en.failedSummary);
  assert.equal(cycleTitle({ status: "interrupted" }), messages.en.interruptedSummary);
  assert.equal(cycleTitle({ status: "unknown" }), messages.en.unknownSummary);
  assert.equal(cycleTitle({ status: "failed", report: '{"private":"raw structure"}' }), messages.en.failedSummary);
  assert.equal(cycleTitle({ summary: "**Verified browser fixture**" }), "Verified browser fixture");
});

test("full report tables retain rows that the summary intentionally abbreviates", () => {
  const { reportRows } = helpers();
  const report = ["| Item | Result |", "| --- | --- |", ...Array.from({ length: 6 }, (_, index) => `| Check ${index + 1} | Passed ${index + 1} |`)].join("\n");
  assert.equal(reportRows({ report }).length, 4);
  const complete = reportRows({ report }, Infinity);
  assert.equal(complete.length, 6);
  assert.equal(complete[5].label, "Check 6");
  assert.equal(complete[5].text, "Passed 6");
});

test("structured task titles preserve meaning while interruption remains a runtime fact", () => {
  const { cycleTitle, statusLabel, messages } = helpers();
  const cycle = { status: "interrupted", events: [{}], summary: "Unrelated legacy sentence",
    workReport: { title: "修复重复键匹配，补齐验证" } };
  assert.equal(cycleTitle(cycle), "修复重复键匹配，补齐验证");
  assert.equal(statusLabel(cycle.status), messages.en.interrupted);
});

test("duration and timestamps never imply a reliable end to interrupted work", () => {
  const { duration, formatTime, messages } = helpers();
  const cycle = { startedAt: "2026-09-18T12:00:00Z", endedAt: "2026-09-18T12:01:30Z", status: "completed" };
  assert.equal(duration(cycle), "1m 30s");
  assert.equal(duration({ ...cycle, durationReliable: false }), "");
  assert.equal(duration({ ...cycle, status: "interrupted" }), "");
  assert.equal(duration({ ...cycle, endedAt: null, status: "running" }), "");
  assert.equal(duration({ ...cycle, endedAt: "2026-09-18T11:59:59Z" }), "");
  assert.equal(formatTime("invalid"), messages.en.unknownTime);
});

test("runtime status labels distinguish unavailable services from unrecorded usage", () => {
  const { state, statusLabel, messages, vocabulary } = helpers();
  const states = ["active", "activating", "configured", "deactivating", "failed", "inactive", "idle", "mismatched", "paused", "waiting_limit", "circuit_break", "not_configured", "not_installed", "reloading", "running", "stopped", "unavailable", "unknown", "unsupported"];
  for (const language of ["en", "zh-CN"]) {
    state.language = language;
    for (const value of states) {
      assert.equal(statusLabel(value), vocabulary.label(value, language) || messages[language][value === "unavailable" ? "statusUnavailable" : value]);
    }
    assert.equal(statusLabel("future_unknown_state"), messages[language].unknown);
    assert.notEqual(statusLabel("unavailable"), messages[language].unavailable);
  }
});

test("day and week usage filters use local ledger dates and retain active coverage", () => {
  const { state, filterUsage, fields } = helpers();
  state.data = { cycles: ["2026-09-13", "2026-09-14", "2026-09-18", "2026-09-20", "2026-09-21"].map((date) => ({ startedAt: new Date(`${date}T12:00:00`).toISOString(), endedAt: new Date(`${date}T12:00:30`).toISOString() })) };
  state.data.cycles.push({ startedAt: new Date("2026-09-17T23:59:30").toISOString(), endedAt: new Date("2026-09-18T00:00:30").toISOString() });
  state.data.cycles.push({ startedAt: new Date("2026-09-20T23:59:30").toISOString(), endedAt: new Date("2026-09-21T00:00:30").toISOString() });
  state.data.cycles.push({ startedAt: new Date("2026-09-18T13:00:00").toISOString(), endedAt: null, active: true, usage: {} });
  fields.get("usageDate").value = "2026-09-18";
  fields.get("usagePeriod").value = "day";
  assert.equal(filterUsage().length, 3);
  fields.get("usagePeriod").value = "week";
  assert.deepEqual(Array.from(filterUsage(), (cycle) => { const date = new Date(cycle.endedAt || cycle.startedAt); return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-'); }), ["2026-09-14", "2026-09-18", "2026-09-20", "2026-09-18", "2026-09-18"]);
  assert.equal(fields.get("usageRange").textContent, new Date().getFullYear() === 2026 ? "09-14 – 09-20" : "2026-09-14 – 2026-09-20");
  fields.get("usagePeriod").value = "all";
  assert.equal(filterUsage().length, 8);
  assert.equal(filterUsage().some((cycle) => cycle.active), true);
  assert.equal(fields.get("usageDate").hidden, true);
});


test("live elapsed time advances only with fresh verified runtime identity", () => {
  const { state, liveDuration } = helpers();
  state.statusFailed = false;
  state.receivedAt = 1000;
  state.data = { runtime: { processState: "running", elapsedReliable: true, elapsedSeconds: 60 } };
  const cycle = { active: true, status: "running" };
  assert.equal(liveDuration(cycle, 4000), "Running for 1m 3s");
  assert.equal(liveDuration(cycle, 17000), "Elapsed time unconfirmed");
  assert.equal(liveDuration(cycle, 999), "Elapsed time unconfirmed");
  state.data.runtime.currentCycleId = "another-cycle";
  assert.equal(liveDuration(cycle, 4000), "Elapsed time unconfirmed");
  delete state.data.runtime.currentCycleId;
  state.statusFailed = true;
  assert.equal(liveDuration(cycle, 4000), "Elapsed time unconfirmed");
  state.statusFailed = false;
  state.data.runtime.elapsedReliable = false;
  assert.equal(liveDuration(cycle, 4000), "Elapsed time unconfirmed");
});

test("check pass counts require a complete internally consistent machine summary", () => {
  const { checkCounts } = helpers();
  assert.equal(checkCounts({ tests: 12, failures: 2, errors: 1, skipped: 3 }).passed, 6);
  assert.equal(checkCounts({ tests: 0, failures: 0, errors: 0, skipped: 0 }).passed, 0);
  assert.equal(checkCounts({ tests: 12, failures: 0 }).passed, undefined);
  assert.equal(checkCounts({ tests: 1, failures: 2, errors: 0, skipped: 0 }).passed, undefined);
  assert.equal(checkCounts(null).passed, undefined);
});


test("project selection never promotes unrelated or unknown history into current work", () => {
  const { latestCycle } = helpers();
  const old = { id: "old", projectStatus: "other", active: false };
  const unknown = { id: "unknown", projectStatus: "unknown", active: false };
  const current = { id: "current", projectStatus: "current", active: false };
  const project = { id: "projects/current" };
  assert.equal(latestCycle({ project, cycles: [old, unknown], latestProjectCycleId: null }), undefined);
  assert.equal(latestCycle({ project, cycles: [old, unknown, current], latestProjectCycleId: "current" }), current);
  assert.equal(latestCycle({ project: { id: null }, cycles: [unknown], latestProjectCycleId: null }), unknown);
  assert.equal(latestCycle({ cycles: [old] }), old);
});

test("product timelines include exploration alongside product, legacy and unknown records", () => {
  const { historyGroups } = helpers();
  const current = { id: "product-5", identityKind: "product" };
  const product = { id: "product-4", identityKind: "product" };
  const exploration = { id: "explore-3", identityKind: "exploration", status: "failed" };
  const legacy = { id: "legacy", numbering: "legacy", status: "unknown" };
  const grouped = historyGroups({ cycles: [current, product, exploration, legacy] }, current);
  assert.deepEqual(Array.from(grouped.main, (cycle) => cycle.id), ["product-4", "explore-3", "legacy"]);

  const explorationCurrent = { id: "explore-4", identityKind: "exploration" };
  const explorationOnly = historyGroups({ cycles: [explorationCurrent, exploration] }, explorationCurrent);
  assert.deepEqual(Array.from(explorationOnly.main, (cycle) => cycle.id), ["explore-3"]);

  const currentExplorationWithProduct = historyGroups({ cycles: [explorationCurrent, product, exploration] }, explorationCurrent);
  assert.deepEqual(Array.from(currentExplorationWithProduct.main, (cycle) => cycle.id), ["product-4", "explore-3"]);
});


test("compact checks never promote stale, incomplete or failed evidence to success", () => {
  const { checkPresentation } = helpers();
  const check = { state: "completed", evidenceStatus: "completed", exitCode: 0, tests: { tests: 7, failures: 0, errors: 0, skipped: 0 } };
  const show = (changes) => checkPresentation({ latestCheck: { ...check, ...changes } });
  assert.equal(show({}).status, "completed");
  assert.equal(show({}).detail, "7 passed");
  for (const changes of [{ evidenceStatus: "missing" }, { freshness: "stale" }, { tests: null }, { exitCode: null }, { evidenceStatus: "unknown" }]) {
    assert.equal(show(changes).status, "unknown");
  }
  assert.equal(show({ exitCode: 1 }).status, "failed");
  assert.match(show({ exitCode: 1 }).detail, /failed/i);
  assert.equal(show({ tests: { tests: 7, failures: 1, errors: 0, skipped: 0 } }).status, "failed");
  assert.equal(show({ state: "interrupted" }).status, "interrupted");
  assert.equal(show({ tests: { tests: 7, failures: 0, errors: 0, skipped: 7 } }).status, "unknown");
  assert.equal(checkPresentation({}), null);
  assert.equal(checkPresentation({ checkStatus: "stale" }).status, "unknown");
});

test("cycle progress distinguishes execution completion, pauses and unknown states", () => {
  const { progressState } = helpers();
  assert.equal(progressState("completed"), "completed");
  assert.equal(progressState("running"), "running");
  assert.equal(progressState("pending"), "pending");
  for (const status of ["interrupted", "paused", "completed_with_timeout"]) assert.equal(progressState(status), "paused");
  for (const status of ["attention", "blocked", "waiting_limit", "circuit_break"]) assert.equal(progressState(status), "attention");
  assert.equal(progressState("failed"), "failed");
  assert.equal(progressState("unexpected"), "unknown");
  assert.equal(progressState(undefined), "unknown");
});

test("unavailable previews use lifecycle labels while documents keep file evidence labels", () => {
  const { state, unavailableArtifact, messages } = helpers();
  for (const language of ["en", "zh-CN"]) {
    state.language = language;
    for (const [status, label] of [["stopped", "previewEnded"], ["interrupted", "previewInterrupted"], ["running", "previewUnavailable"], ["launch_failed", "previewUnavailable"]]) {
      assert.equal(unavailableArtifact({ kind: "preview", state: status, evidenceStatus: "stale" }), messages[language][label]);
    }
    assert.equal(unavailableArtifact({ kind: "document", evidenceStatus: "stale" }), messages[language].artifactStale);
  }
});

function scopedUsageHarness() {
  const fields = new Map(['usagePeriod', 'usageDate', 'refreshButton', 'refreshStatus', 'autoRefresh', 'connectionError', 'loadingState'].map((id) => [id, {}]));
  fields.get('usagePeriod').value = 'all';
  fields.get('usageDate').value = '2026-10-01';
  const requests = [];
  const renders = [];
  const context = vm.createContext({ window: { scrollY: 0, scrollTo() {} }, location: { pathname: '/products/entry-a' },
    document: { getElementById(id) { assert.ok(fields.has(id), id); return fields.get(id); } },
    clearTimeout() {}, performance: { now: () => 0 }, requestAnimationFrame: (callback) => callback(),
    request: (url) => new Promise((resolve, reject) => requests.push({ url, resolve, reject })),
    recordUsage: (usage) => renders.push(usage),
  });
  registerJournal(context);
  vm.runInContext(i18n, context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "date-time.js"), "utf8"), context);
  const binding = app.indexOf("\n  document.querySelectorAll('[data-tab]').forEach");
  // Keep the real refresh, pagination, usage validation and response guards.
  // Replace only I/O, rendering and the background timer for deterministic races.
  vm.runInContext(app.slice(0, binding) + `
    fetchCenter = globalThis.request;
    render = renderRuntime = renderSidebar = refreshCenterContext = scheduleRefresh = connectionNotice = () => {};
    renderUsage = () => globalThis.recordUsage(state.scopedUsage);
    globalThis.journal = { state, refresh, refreshScopedUsage, refreshMedia, loadCycleDetail, projection, retainHistoricalCycles, usageRowFresh };
  });`, context);
  const snapshot = { ok: true, entryId: 'entry-a', sourceId: 'source-a', sourceRevision: 1, cycles: [], total: 0, generatedAt: '2026-10-01T00:00:00Z' };
  context.journal.state.data = snapshot;
  const usage = { entryId: 'entry-a', sourceId: 'source-a', sourceRevision: 1, period: 'all', startDate: null, endDate: null, usage: { totalTokens: 42 }, recorded: 1, unknown: 0 };
  return { ...context.journal, fields, requests, renders, snapshot, usage };
}

for (const outcome of ['failure', 'success']) {
  test(`late usage ${outcome} cannot replace a completed journal refresh`, async () => {
    const h = scopedUsageHarness();
    const old = h.refreshScopedUsage();
    const fresh = h.refresh();
    assert.equal(h.requests.length, 2);
    h.requests[1].resolve({ ...h.snapshot, sourceRevision: 2, generatedAt: '2026-10-01T00:00:05Z' });
    // Wait for the real journal refresh to request its scoped ledger.
    for (let turn = 0; h.requests.length < 3 && turn < 10; turn++) await Promise.resolve();
    assert.equal(h.requests.length, 3);
    h.requests[2].resolve({ ...h.usage, sourceRevision: 2 });
    await fresh;
    await h.refreshScopedUsage();
    assert.equal(h.state.statusFailed, false);
    const installed = h.state.scopedUsage;
    assert.equal(installed.data.usage.totalTokens, 42);
    const rendered = h.renders.length;
    if (outcome === 'failure') h.requests[0].reject(new Error('old request failed'));
    else h.requests[0].resolve({ ...h.usage, usage: { totalTokens: 7 } });
    await old;
    assert.equal(h.state.scopedUsage, installed);
    assert.equal(h.renders.length, rendered);
  });
}

test('current usage failure marks an unavailable scope without borrowing another scope', async () => {
  const h = scopedUsageHarness();
  h.state.scopedUsage = { key: 'previous', data: h.usage };
  const pending = h.refreshScopedUsage();
  h.requests[0].reject(new Error('current request failed'));
  await pending;
  assert.equal(h.state.scopedUsage.data, null);
  assert.equal(h.state.scopedUsage.stale, true);
  assert.equal(h.renders.length, 1);
});

test('v2 core advances while usage and media are pending or fail', async () => {
  const h = scopedUsageHarness();
  const data = { ...h.snapshot, projectionVersion: 2, centerId: 'center', sourceBindingVersion: 'binding',
    productId: 'product', explorationId: null, projectionEpoch: 'epoch', snapshotRevision: 1,
    currentCycleId: 'new-cycle', cycles: [{ id: 'new-cycle', protocolState: 'closed', outcome: 'completed', status: 'completed', attempts: [] }],
    partitions: Object.fromEntries(['report', 'checks', 'events', 'media', 'usage', 'history', 'runtime'].map(kind => [kind, { revision: 1, status: 'available' }])) };
  const first = h.refresh(); h.requests[0].resolve(data); await first;
  assert.equal(h.state.data.currentCycleId, 'new-cycle');
  assert.equal(h.state.statusFailed, false);
  assert.equal(h.requests.length, 3);
  const usage = h.refreshScopedUsage(), media = h.refreshMedia();
  const next = h.refresh(); h.requests[3].resolve({ ...data, sourceRevision: 2, snapshotRevision: 2, currentCycleId: 'newer-cycle', cycles: [{ ...data.cycles[0], id: 'newer-cycle' }] });
  await next;
  assert.equal(h.state.data.currentCycleId, 'newer-cycle');
  h.requests[1].reject(new Error('usage offline')); h.requests[2].reject(new Error('media offline'));
  await Promise.all([usage, media]);
  // media uses its existing in-flight read; let its finally handler settle.
  await Promise.resolve();
  assert.equal(h.state.statusFailed, false);
  assert.equal(h.state.data.currentCycleId, 'newer-cycle');
  assert.equal(h.state.scopedUsage.stale, true);
  assert.equal(h.state.data.partitions.media.status, 'unavailable');
});

test('late historical usage installs from detail while unread history remains explicitly stale', async () => {
  const h = scopedUsageHarness();
  const row = (id, tokens = 100, revision = 1) => ({ id, status: 'completed', protocolState: 'closed', activeAttemptId: null,
    detailStatus: 'recorded', usage: { totalTokens: tokens, status: 'available' }, costUsd: tokens === 900 ? 8.5 : .5, costStatus: 'reported',
    partitions: { usage: { revision, status: 'available', freshness: 'fresh', asOf: '2026-10-23T01:00:00Z' },
      report: { errorCode: 'NOT_REQUESTED' }, documents: { errorCode: 'NOT_REQUESTED' }, events: { errorCode: 'NOT_REQUESTED' } } });
  const recent = { ...h.snapshot, projectionVersion: 2, centerId: 'center', sourceBindingVersion: 1, projectionEpoch: 'epoch',
    snapshotRevision: 1, currentCycleId: '22', cycles: Array.from({ length: 20 }, (_, i) => row(String(22 - i))), total: 22 };
  h.projection.core(recent);
  h.state.data = { ...recent, cycles: [...recent.cycles, row('2'), row('1')] };
  const detail = { ...recent, ...row('1', 900, 2), cycles: undefined };
  const pending = h.loadCycleDetail('1', true);
  h.requests[0].resolve(detail); await pending;
  assert.equal(h.state.data.cycles.at(-1).usage.totalTokens, 900);
  assert.equal(h.state.data.cycles.at(-1).costUsd, 8.5);
  assert.equal(h.usageRowFresh(h.state.data.cycles.at(-1)), true);
  const refreshed = h.refresh(); h.requests[1].resolve(structuredClone(recent)); await refreshed;
  const historical = h.state.data.cycles.find(cycle => cycle.id === '1');
  assert.equal(h.state.data.cycles.length, 22);
  assert.equal(historical.usage.totalTokens, 900);
  assert.equal(h.usageRowFresh(historical), false);
  assert.equal(historical.partitions.usage.freshness, 'stale');
  // A late older detail must not replace the already installed accounting.
  const delayed = h.loadCycleDetail('1', true);
  h.requests.at(-1).resolve({ ...detail, ...row('1', 100, 1) }); await delayed;
  const preserved = h.state.data.cycles.find(cycle => cycle.id === '1');
  assert.equal(preserved.usage.totalTokens, 900);
  assert.equal(preserved.costUsd, 8.5);
  assert.equal(preserved.partitions.usage.errorCode, 'REVISION_CONFLICT');
});

for (const change of ['new request', 'selection']) {
  test(`late usage failure respects a newer ${change}`, async () => {
    const h = scopedUsageHarness();
    const old = h.refreshScopedUsage();
    h.fields.get('usagePeriod').value = 'day';
    const retained = { key: 'newer selection', data: h.usage };
    if (change === 'new request') {
      const current = h.refreshScopedUsage();
      h.requests[1].resolve({ ...h.usage, period: 'day', startDate: '2026-10-01', endDate: '2026-10-01' });
      await current;
    } else h.state.scopedUsage = retained;
    const installed = h.state.scopedUsage;
    const rendered = h.renders.length;
    h.requests[0].reject(new Error('old filter failed'));
    await old;
    assert.equal(h.state.scopedUsage, installed);
    assert.equal(h.renders.length, rendered);
  });
}

function logSourceHarness() {
  const fields = new Map(['logText', 'rawLogText', 'copyLogButton', 'downloadLogButton', 'downloadFullLogButton', 'logSearch', 'previousLogMatch', 'nextLogMatch', 'logMatchStatus', 'refreshLogButton', 'logStatus', 'newLogButton', 'followLog'].map((id) => [id, {}]));
  fields.get('logSearch').value = '';
  fields.get('logText').replaceChildren = function(fragment) {
    this.textContent = (fragment?.children || []).map((child) => child.textContent).join('');
    this.marks = (fragment?.children || []).filter((child) => child.tag === 'mark');
  };
  fields.get('logText').querySelector = function(selector) {
    return selector === '.log-current-match' ? (this.marks || []).find((mark) => mark.className === 'log-current-match') || null : null;
  };
  const reads = [], centerReads = [], downloads = [];
  const context = vm.createContext({ window: {}, location: { pathname: '/products/entry-a' },
    document: {
      getElementById(id) { assert.ok(fields.has(id), id); return fields.get(id); },
      createDocumentFragment: () => ({ children: [], append(node) { this.children.push(node); } }),
      createTextNode: (textContent) => ({ textContent }),
    },
    read: (url) => new Promise((resolve, reject) => reads.push({ url, resolve, reject })),
    centerRead: (path) => centerReads.shift()(path),
    downloads,
    atob: (value) => Buffer.from(value, 'base64').toString('binary'),
    Uint8Array, Buffer,
  });
  registerJournal(context);
  context.window.DashboardUI ||= {};
  context.window.DashboardUI.element = (tag, className, textContent = '') => ({ tag, className, textContent, scrollIntoView() {} });
  vm.runInContext(i18n, context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "date-time.js"), "utf8"), context);
  const binding = app.indexOf("\n  document.querySelectorAll('[data-tab]').forEach");
  vm.runInContext(app.slice(0, binding) + '\n fetchScopedText = globalThis.read; fetchCenter = globalThis.centerRead; saveLogDownload = (parts, name) => globalThis.downloads.push({ parts, name }); globalThis.journal = {state, loadLog, renderLogSearch, downloadFullLog};\n});', context);
  const snapshot = (source, revision = 1, resource = 'log-same-cycle') => ({ entryId: 'entry-a', sourceId: source, sourceRevision: revision,
    cycles: [{ id: 'same-cycle', logUrl: `/api/center/v1/entries/entry-a/resources/${resource}?sourceId=${source}` }] });
  context.journal.state.data = snapshot('source-a');
  context.journal.state.selectedLog = 'same-cycle';
  return { ...context.journal, fields, reads, centerReads, downloads, snapshot };
}

for (const outcome of ['success', 'failure']) {
  test(`source change ignores old log ${outcome} and reads the current source`, async () => {
    const h = logSourceHarness();
    const old = h.loadLog();
    h.state.data = h.snapshot('source-b');
    const current = h.loadLog();
    assert.equal(h.reads.length, 1, 'reads remain serialized');
    if (outcome === 'success') h.reads[0].resolve('SOURCE A');
    else h.reads[0].reject(new Error('A unavailable'));
    await old;
    for (let turn = 0; h.reads.length < 2 && turn < 10; turn++) await Promise.resolve();
    assert.equal(h.reads.length, 2, 'same cycle in B needs its own read');
    assert.match(h.reads[1].url, /sourceId=source-b$/);
    assert.notEqual(h.fields.get('logText').textContent, 'SOURCE A');
    assert.ok(h.state.logPending, 'old cleanup must not remove B pending');
    assert.equal(h.fields.get('copyLogButton').disabled, true);
    h.reads[1].resolve('SOURCE B');
    await current;
    assert.equal(h.fields.get('logText').textContent, 'SOURCE B');
    assert.equal(h.state.logText, 'SOURCE B');
    assert.equal(h.state.logPending, null);
  });
}

for (const change of ['source', 'revision', 'resource']) {
  test(`loaded log cache is not reused after a ${change} change`, async () => {
    const h = logSourceHarness();
    const initial = h.loadLog(); h.reads[0].resolve('SOURCE A'); await initial;
    h.state.data = h.snapshot(change === 'source' ? 'source-b' : 'source-a', change === 'revision' ? 2 : 1, change === 'resource' ? 'log-new-resource' : 'log-same-cycle');
    const pending = h.loadLog();
    assert.equal(h.fields.get('logText').textContent, '');
    assert.equal(h.fields.get('rawLogText').textContent, '');
    h.reads[1].reject(new Error('new context unavailable'));
    await pending;
    assert.equal(h.state.logText, '');
    assert.equal(h.fields.get('logText').textContent, '');
  });
}

test('same log context deduplicates reads and retains its own text on failure', async () => {
  const h = logSourceHarness();
  const first = h.loadLog(); const duplicate = h.loadLog();
  assert.equal(h.reads.length, 1);
  h.reads[0].resolve('CURRENT'); await Promise.all([first, duplicate]);
  h.state.data = h.snapshot('source-a'); // Normal poll replaces the object, not its identity fields.
  const retry = h.loadLog();
  assert.equal(h.fields.get('logText').textContent, 'CURRENT');
  assert.equal(h.fields.get('copyLogButton').disabled, false);
  assert.ok(h.state.logLoadedAt);
  h.reads[1].reject(new Error('current failure')); await retry;
  assert.match(h.fields.get('logStatus').textContent, /Last successful read|最后成功读取/);
  assert.equal(h.state.logText, 'CURRENT');
  assert.equal(h.fields.get('logText').textContent, 'CURRENT');
});

test('source change clears already displayed old text while waiting for the old read', async () => {
  const h = logSourceHarness();
  const initial = h.loadLog(); h.reads[0].resolve('SOURCE A'); await initial;
  const old = h.loadLog();
  h.state.data = h.snapshot('source-b');
  const current = h.loadLog();
  assert.equal(h.fields.get('logText').textContent, '');
  assert.equal(h.state.logText, '');
  assert.equal(h.fields.get('copyLogButton').disabled, true);
  h.reads[1].resolve('OLD A REFRESH'); await old;
  for (let turn = 0; h.reads.length < 3 && turn < 10; turn++) await Promise.resolve();
  assert.equal(h.reads.length, 3);
  h.reads[2].resolve('SOURCE B'); await current;
  assert.equal(h.state.logText, 'SOURCE B');
});

test("cycle labels use authoritative continuous numbers and retain legacy fallback", () => {
  const { paddedCycleNumber } = helpers();
  assert.equal(paddedCycleNumber({ sequenceNumber: 7, number: 4 }), "07");
  assert.equal(paddedCycleNumber({ sequenceNumber: null, number: 4 }), "04");
  assert.equal(paddedCycleNumber({ number: 1 }), "01");
});

test('structured logs read as cycle text, commands and failures without transport JSON', () => {
  const { readableLog } = helpers();
  const events = [
    { type: 'thread.started', thread_id: 'private-id' },
    { type: 'item.started', item: { id: 'cmd', type: 'command_execution', command: 'check products' } },
    { type: 'item.completed', item: { id: 'cmd', type: 'command_execution', command: 'check products', aggregated_output: '2 checks failed', exit_code: 1 } },
    { type: 'item.completed', item: { type: 'agent_message', text: '<script>plain report text</script>' } },
    { type: 'turn.failed', error: { message: 'connection lost' } },
  ];
  const text = readableLog('Reading additional input from stdin...\n' + events.map(event => JSON.stringify(event)).join('\n'), { number: 5, startedAt: '2026-09-27T01:32:16Z' });
  assert.match(text, /#05/);
  assert.equal(text.split('$ check products').length, 2);
  assert.match(text, /2 checks failed/);
  assert.match(text, /Exit code: 1/);
  assert.match(text, /<script>plain report text<\/script>/);
  assert.match(text, /connection lost/);
  assert.doesNotMatch(text, /thread_id|aggregated_output|stdin/);
  assert.equal(readableLog('Cycle #1\nnormal text'), 'Cycle #1\nnormal text');
});


test('file changes and collaboration remain readable while raw events retain their detail', () => {
  const { readableLog } = helpers();
  const value = readableLog(JSON.stringify({ type: 'item.completed', item: { type: 'file_change', changes: [{ path: 'src/report.js', kind: 'update' }] } }) + '\n' +
    JSON.stringify({ type: 'item.completed', item: { type: 'collab_agent_tool_call', tool: 'spawn_agent', status: 'completed' } }));
  assert.match(value, /src\/report.js/);
  assert.match(value, /spawn_agent/);
  assert.doesNotMatch(value, /item.completed/);
});

test('log search highlights matches, navigates cycling index and full log download verifies revision continuity', async () => {
  const h = logSourceHarness();
  h.state.language = 'en';
  const load = h.loadLog();
  h.reads[0].resolve('alpha beta alpha gamma alpha');
  await load;
  assert.equal(h.fields.get('downloadLogButton').disabled, false);
  assert.equal(h.fields.get('downloadFullLogButton').disabled, false);
  h.fields.get('logSearch').value = 'ALPHA';
  h.renderLogSearch();
  assert.equal(h.fields.get('logText').marks.length, 3);
  assert.equal(h.fields.get('logText').marks[0].className, 'log-current-match');
  assert.equal(h.fields.get('logMatchStatus').textContent, '1 / 3 matches');
  h.renderLogSearch(-1);
  assert.equal(h.fields.get('logMatchStatus').textContent, '3 / 3 matches');
  assert.equal(h.fields.get('logText').marks[2].className, 'log-current-match');

  h.centerReads.push(async (path) => {
    assert.match(path, /\/entries\/entry-a\/logs\/same-cycle\?sourceId=source-a&offset=0&limit=131072$/);
    return { ok: true, offset: 0, nextOffset: 5, totalBytes: 8, eof: false, revision: '8:100', bytesBase64: Buffer.from('hello').toString('base64') };
  });
  h.centerReads.push(async (path) => {
    assert.match(path, /&offset=5&limit=131072&revision=8%3A100$/);
    return { ok: true, offset: 5, nextOffset: 8, totalBytes: 8, eof: true, revision: '8:100', bytesBase64: Buffer.from('bye').toString('base64') };
  });
  await h.downloadFullLog();
  assert.equal(h.downloads.length, 1);
  assert.equal(h.downloads[0].name, 'same-cycle-full-raw.log');
  assert.equal(Buffer.concat(h.downloads[0].parts.map(Buffer.from)).toString('utf8'), 'hellobye');
  assert.match(h.fields.get('logStatus').textContent, /Full raw log downloaded/);
});

test('fast all -> day -> all usage toggle resolves with valid all payload without getting stuck', async () => {
  const h = scopedUsageHarness();
  const firstAll = h.refreshScopedUsage();
  h.fields.get('usagePeriod').value = 'day';
  h.fields.get('usageDate').value = '2026-10-01';
  const dayReq = h.refreshScopedUsage();
  h.fields.get('usagePeriod').value = 'all';
  h.fields.get('usageDate').value = '';
  const secondAll = h.refreshScopedUsage();
  assert.equal(h.requests.length, 2);
  h.requests[1].resolve({ ...h.usage, period: 'day', startDate: '2026-10-01', endDate: '2026-10-01', usage: { total_tokens: 99 } });
  await dayReq;
  h.requests[0].resolve({ ...h.usage, period: 'all', usage: { total_tokens: 555 } });
  await Promise.all([firstAll, secondAll]);
  assert.equal(h.state.scopedUsage?.key, '[["entry-a","source-a",1],null,"all",""]');
  assert.equal(h.state.scopedUsage?.data?.usage?.total_tokens, 555);
});
