const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const dashboard = path.resolve(__dirname, "../dashboard");
const html = fs.readFileSync(path.join(dashboard, "center.html"), "utf8");
const app = fs.readFileSync(path.join(dashboard, "center.js"), "utf8");
const i18n = fs.readFileSync(path.join(dashboard, "center-i18n.js"), "utf8");
const journalHTML = fs.readFileSync(path.join(dashboard, "index.html"), "utf8");
const journalApp = fs.readFileSync(path.join(dashboard, "app.js"), "utf8");

function helpers() {
  const context = vm.createContext({
    window: {}, location: { pathname: "/center", origin: "http://127.0.0.1:8842" },
    document: { documentElement: { lang: "en" } }, URL, Intl, Date, Number, Object, Set, Map, String, Math, AbortController, setTimeout: () => 1, clearTimeout() {},
    crypto: { randomUUID: (() => { let value = 0; return () => `intent-${++value}`; })() },
  });
  vm.runInContext(i18n, context);
  context.window.DashboardNavigation = { register(_kind, mount) { mount({ document: context.document, ui: (context.window.DashboardUI ||= {}), active: true, url: 'http://127.0.0.1:8842/center', listen() {}, request: () => ({ valid: () => true, done() {} }) }); } };
  vm.runInContext(fs.readFileSync(path.join(dashboard, "icons.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "date-time.js"), "utf8"), context);
  const binding = app.lastIndexOf("\n  applyLanguage(); wire(); renderPage(); refresh();");
  assert.ok(binding > 0, "Center event wiring must follow helper declarations");
  vm.runInContext(app.slice(0, binding) + "\n globalThis.center = { state, message, entryState, capability, capabilityReason, errorText, requestReason, requestIsFresh, executionBlockReason, requestDisplayState, requestOwnsDispatch, normalizeCounts, renderCounts, filteredEntries, sortedEntries, latestWorkSource, readonlyObservationState, emptyListState, requestState, statusLabel, write, wire, submitProbe, renderEntries, renderQueue, setRenderPage: callback => { renderPage = callback; } };\n});", context);
  context.center.state.language = "en";
  return { ...context.center, messages: context.window.CENTER_MESSAGES, context };
}

function journalHelpers() {
  const context = vm.createContext({
    window: {}, location: { pathname: "/products/entry-a", origin: "http://127.0.0.1:8843" },
    document: { documentElement: { lang: "en" } }, URL, Intl, Date, Number, Object, Set, Map, String, Math, AbortController, setTimeout, clearTimeout,
  });
  vm.runInContext(fs.readFileSync(path.join(dashboard, "i18n.js"), "utf8"), context);
  context.window.DashboardNavigation = { register(_kind, mount) { mount({ document: context.document, ui: (context.window.DashboardUI ||= {}), active: true, url: 'http://127.0.0.1:8843/products/entry-a', listen() {}, request: () => ({ valid: () => true, done() {} }) }); } };
  vm.runInContext(fs.readFileSync(path.join(dashboard, "icons.js"), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, "date-time.js"), "utf8"), context);
  const binding = journalApp.indexOf("\n  document.querySelectorAll('[data-tab]')");
  assert.ok(binding > 0, "Journal event wiring must follow helper declarations");
  vm.runInContext(journalApp.slice(0, binding) + "\n globalThis.journal = { state, scope, freshCenterRequest, centerRequestDisplayState, scopedCenterRuntimeState, scopedRecordedRuntimeState, runtimeStateValue, runtimeStatusLabel, runtimeLabel, requestContextLabel, centerRuntimeContextValue, historyGroups, fetchFullScopedJournal, journalPageMatches, safePreviewURL };\n});", context);
  context.journal.state.language = "en";
  return { ...context.journal, context };
}

test("queue badge counts requests without treating read-only unknown products as queued work", () => {
  const { state, context, renderCounts } = helpers();
  const elements = {};
  context.document.getElementById = id => elements[id] ||= { replaceChildren() { this.textContent = ""; }, append(node) { this.textContent += node.textContent; } };
  context.window.DashboardUI.element = (tag, className, text) => ({ textContent: text });
  state.entries = [1, 2, 3].map(id => ({ entryId: `archive-${id}`, kind: "product", executionSummary: { state: "unknown" } }));
  state.summary = { currentRequest: { requestId: "active", state: "running" }, queuedCount: 0, attentionCount: 0 };
  renderCounts();
  assert.equal(elements.countAttention.textContent, "3");
  assert.equal(elements.queueNavCount.textContent, "1");
  state.summary = { currentRequest: { requestId: "active", state: "attention" }, queuedCount: 0, attentionCount: 1 };
  renderCounts();
  assert.equal(elements.queueNavCount.textContent, "1");
  state.summary = { currentRequest: null, queuedCount: 0, attentionCount: 0 };
  renderCounts();
  assert.equal(elements.queueNavCount.hidden, true);
});

test("center fixed labels are complete and bilingual", () => {
  const { messages } = helpers();
  assert.deepEqual(Object.keys(messages.en).sort(), Object.keys(messages["zh-CN"]).sort());
  const placeholders = (value) => [...value.matchAll(/\{([a-zA-Z]+)\}/g)].map((match) => match[1]).sort();
  for (const key of Object.keys(messages.en)) {
    assert.ok(messages.en[key] && messages["zh-CN"][key], `Empty translation: ${key}`);
    assert.deepEqual(placeholders(messages.en[key]), placeholders(messages["zh-CN"][key]), key);
  }
  const rendered = [...html.matchAll(/data-i18n(?:-placeholder|-aria)?="([^"]+)"/g), ...app.matchAll(/message\("([^"]+)"/g)];
  for (const [, key] of rendered) assert.ok(messages.en[key], `Missing rendered translation: ${key}`);
});

test("column ordering uses the whole filtered result before grouping and preserves unavailable values", () => {
  const { state, sortedEntries, filteredEntries } = helpers();
  state.entries = [
    { entryId: "a", kind: "product", displayName: "Zeta", cycleNumber: 9, latestCycleStatus: "completed", lastActivityAt: "2026-10-01T00:00:00Z" },
    { entryId: "b", kind: "product", displayName: "Alpha", cycleNumber: 2, latestCycleStatus: "failed", lastActivityAt: null },
    { entryId: "c", kind: "product", displayName: "Beta", latestCycleStatus: "completed", lastActivityAt: "2026-10-02T00:00:00Z" },
  ];
  state.sort = "name"; state.sortDirection = "asc";
  assert.deepEqual(Array.from(sortedEntries(), row => row.entryId), ["b", "c", "a"]);
  state.sort = "round"; state.sortDirection = "desc";
  assert.deepEqual(Array.from(sortedEntries(), row => row.entryId), ["a", "b", "c"]);
  state.roundFilter = "completed";
  assert.deepEqual(Array.from(filteredEntries(), row => row.entryId), ["a", "c"]);
  state.sort = "activity"; state.sortDirection = "asc"; state.roundFilter = "all";
  assert.deepEqual(Array.from(sortedEntries(), row => row.entryId), ["a", "c", "b"]);
});

test("runtime filters use fresh source observations while preserving read-only access", () => {
  const { state, entryState, filteredEntries, normalizeCounts, readonlyObservationState, latestWorkSource } = helpers();
  const states = ["read_only", "paused", "ended", "idle", "unknown", "failed", "canceled", "preparing"];
  state.entries = states.map(value => ({ entryId: value, kind: "product", executionSummary: { state: value } }));
  for (const value of states) { state.filter = value; assert.deepEqual(Array.from(filteredEntries(), entry => entry.entryId), value === "unknown" ? ["read_only", "unknown"] : [value]); }
  state.filter = "invalid-filter"; assert.equal(filteredEntries().length, 0);
  const now = Date.now(), source = { readonlyObservation: { state: "running", readOnly: true, scoped: true, liveConfirmedAt: new Date(now - 1000).toISOString() } };
  Object.assign(state.entries[0], source);
  assert.equal(readonlyObservationState(state.entries[0], now), "running");
  assert.equal(entryState(state.entries[0], now), "running");
  assert.equal(entryState(state.entries[0], now + 15000), "unknown");
  assert.equal(normalizeCounts().running, 1);
  assert.equal(readonlyObservationState(state.entries[0], now + 15000), "");
  assert.equal(readonlyObservationState({ readonlyObservation: { ...source.readonlyObservation, scoped: false } }, now), "");
  assert.equal(readonlyObservationState({ readonlyObservation: { state: "ended", readOnly: true, scoped: true, processState: "stopped", observedAt: new Date(now).toISOString() } }, now), "ended");
  assert.equal(latestWorkSource({ latestWork: { scope: "exploration", cycleNumber: 5, isLatestCycle: false } }), "Exploration record · Cycle 05");
  assert.equal(latestWorkSource({ latestWork: { scope: "product", cycleNumber: 7, isLatestCycle: true } }), "");
  assert.equal(latestWorkSource({ latestWork: { scope: "product", cycleNumber: 6, isLatestCycle: false } }), "Earlier work record · Cycle 06");
});

test("round filters match startup reservations without changing their raw status", () => {
  const { state, filteredEntries, sortedEntries } = helpers();
  state.entries = ["not_started", "startup_unconfirmed", "unknown", "pending"].map(value => ({ entryId: value, kind: "product", cycleNumber: 1, latestCycleStatus: value, lastActivityAt: "2026-10-03T00:00:00Z" }));
  for (const value of ["not_started", "startup_unconfirmed", "unknown", "pending"]) { state.roundFilter = value; assert.deepEqual(Array.from(filteredEntries(), entry => entry.entryId), [value]); }
  state.roundFilter = "all";
  assert.deepEqual(Array.from(sortedEntries(), entry => entry.entryId), ["not_started", "startup_unconfirmed", "unknown", "pending"], "Equal activity timestamps retain API order");
  state.entries[1].readonlyObservation = { readOnly: true, scoped: true, state: "ended", processState: "stopped", observedAt: new Date().toISOString() };
  state.roundFilter = "interrupted";
  assert.deepEqual(Array.from(filteredEntries(), entry => entry.entryId), ["startup_unconfirmed"]);
  assert.equal(state.entries[1].latestCycleStatus, "startup_unconfirmed", "Display projection must preserve the ledger status");
});

test("parallel projects use their own live request and include active exploration", () => {
  const { state, entryState, filteredEntries, normalizeCounts, renderCounts, context } = helpers();
  const fresh = new Date().toISOString();
  const requests = ["a", "b"].map(id => ({ requestId: `request-${id}`, entryId: `entry-${id}`, state: "running", liveConfirmedAt: fresh }));
  state.requests = requests;
  state.summary = { currentRequest: requests[0], currentRequests: requests, queuedCount: 1, attentionCount: 1 };
  state.entries = requests.map((request, index) => ({ entryId: request.entryId, kind: index ? "exploration" : "product", executionSummary: request }));
  state.entries.push({ entryId: "historical-exploration", kind: "exploration" });
  assert.equal(entryState(state.entries[1]), "running");
  assert.equal(filteredEntries().length, 3);
  assert.equal(normalizeCounts().running, 2);
  const elements = {};
  context.document.getElementById = id => elements[id] ||= { replaceChildren() { this.textContent = ""; }, append(node) { this.textContent += node.textContent; } };
  context.window.DashboardUI.element = (tag, className, text) => ({ textContent: text });
  renderCounts();
  assert.equal(elements.queueNavCount.textContent, "4");
  requests[1].liveConfirmedAt = "2000-01-01T00:00:00Z";
  assert.equal(entryState(state.entries[1]), "unknown");
});

test("a product journal finds its own request among simultaneous owners", () => {
  const { state, freshCenterRequest } = journalHelpers();
  state.statusFailed = false;
  state.data = { entry: { entryId: "entry-a" } };
  const first = { entryId: "other-entry", state: "running", liveConfirmedAt: new Date().toISOString() };
  const own = { ...first, entryId: "entry-a" };
  state.centerSummary = { currentRequest: first, currentRequests: [first, own] };
  assert.equal(freshCenterRequest(), own);
});

test("entry state preserves unknown and keeps archive separate from execution", () => {
  const { state, entryState, statusLabel, messages } = helpers();
  const now = Date.now();
  state.summary = { currentRequest: { requestId: "request-a", entryId: "entry-a", state: "running", liveConfirmedAt: new Date(now - 1000).toISOString() } };
  assert.equal(entryState({ archived: true, executionSummary: { state: "running" } }), "archived");
  assert.equal(entryState({ entryId: "entry-a", executionSummary: { requestId: "request-a", state: "running" } }, now), "running");
  assert.equal(entryState({ entryId: "entry-b", executionSummary: { requestId: "request-b", state: "running" } }, now), "unknown");
  assert.equal(entryState({ executionSummary: { state: "queued" } }), "queued");
  assert.equal(entryState({ executionSummary: { state: "ended" } }), "ended");
  assert.equal(entryState({ executionSummary: { state: "unknown" } }), "unknown");
  assert.equal(entryState({ availability: { state: "conflict" }, capabilities: { execute: false }, executionSummary: { state: "idle" } }), "unknown");
  assert.equal(entryState({ availability: "read_only", capabilities: { execute: false }, executionSummary: { state: "idle" } }), "unknown");
  assert.equal(entryState({ availability: "available", executionSummary: {} }), "idle");
  assert.equal(statusLabel("future-state"), messages.en.state_unknown);
});

test("capability reasons remain visible independently of the boolean", () => {
  const { capability } = helpers();
  assert.deepEqual({ ...capability({ capabilities: { execute: true } }, "execute") }, { enabled: true, reason: "" });
  assert.deepEqual({ ...capability({ capabilities: { execute: false }, capabilityReasons: { execute: "READ_ONLY_SOURCE" } }, "execute") }, { enabled: false, reason: "READ_ONLY_SOURCE" });
  assert.deepEqual({ ...capability({ capabilities: { execute: { enabled: false, reason: "SOURCE_CONFLICT" } } }, "execute") }, { enabled: false, reason: "SOURCE_CONFLICT" });
});

test("execution preflight failures use fixed bilingual guidance instead of internal codes", () => {
  const { state, capabilityReason, errorText, requestReason } = helpers();
  const english = {
    registration: "The product registration does not match the current source. Restore or reconnect the registration before continuing.",
    context: "The product identity or run records required to continue cannot be verified. Restore the source state first.",
  };
  assert.equal(capabilityReason("product_registration_invalid"), english.registration);
  assert.equal(errorText({ code: "PRODUCT_REGISTRATION_INVALID", message: "technical fallback" }), english.registration);
  assert.equal(capabilityReason("context_unavailable"), english.context);
  assert.equal(errorText({ code: "CONTEXT_UNAVAILABLE" }), english.context);
  assert.equal(requestReason("PRODUCT_REGISTRATION_INVALID"), english.registration);
  assert.equal(requestReason("CONTEXT_UNAVAILABLE"), english.context);
  assert.equal(capabilityReason("governance_pause"), "Governance protection paused execution");
  assert.equal(capabilityReason("budget_pause"), "Budget protection paused execution");
  assert.equal(capabilityReason("stop_unconfirmed"), "Stop is not confirmed");
  assert.equal(requestReason("user_stop"), "Stopped as requested");
  assert.equal(requestReason("user_cancel"), "Queued request canceled");
  state.language = "zh-CN";
  assert.equal(capabilityReason("product_registration_invalid"), "产品登记与当前源码不一致。请恢复或重新连接登记后再继续。");
  assert.equal(requestReason("CONTEXT_UNAVAILABLE"), "无法核对继续工作所需的产品身份或运行记录。请先恢复来源状态。");
  assert.doesNotMatch(capabilityReason("product_registration_invalid"), /product_registration_invalid/i);
  assert.match(app, /const previewStop = capability\(entry, "previewStop"\)/);
  assert.match(app, /"previewStop", current && previewStop\.enabled/);
});

test("live unresolved P1 projects as blocked while preserving the raw running request", () => {
  const { state, requestState, executionBlockReason, requestDisplayState, entryState, capabilityReason, errorText, requestReason, statusLabel, filteredEntries, normalizeCounts } = helpers();
  const now = Date.now();
  const request = { requestId: "request-blocked", entryId: "blocked", state: "running", liveConfirmedAt: new Date(now - 1000).toISOString(), executionBlockedReason: "unresolved_p1", executionBlockedAt: new Date(now - 2000).toISOString() };
  state.stale = false;
  state.summary = { currentRequest: request, attentionCount: 0, counts: { attention: 0 } };
  assert.equal(requestState(request), "running", "Queue controls must retain the raw slot-owning state");
  assert.equal(executionBlockReason(request, now), "unresolved_p1");
  assert.equal(requestDisplayState(request, now), "blocked");
  assert.equal(statusLabel("blocked"), "Protection paused");
  const blockedEntry = { entryId: "blocked", kind: "product", archived: false, executionSummary: { requestId: "request-blocked", state: "blocked", reason: "unresolved_p1" } };
  assert.equal(entryState(blockedEntry, now), "blocked");
  assert.equal(capabilityReason("unresolved_p1"), "An unresolved P1 issue is waiting for a human decision before work can continue.");
  assert.equal(errorText({ code: "UNRESOLVED_P1" }), "An unresolved P1 issue is waiting for a human decision before work can continue.");
  assert.equal(requestReason("UNRESOLVED_P1"), "An unresolved P1 issue is waiting for a human decision before work can continue.");
  state.entries = [blockedEntry]; state.filter = "attention";
  assert.deepEqual(Array.from(filteredEntries(), entry => entry.entryId), ["blocked"]);
  assert.equal(normalizeCounts().attention, 1, "Product filter counts must not be overwritten by raw request summary counts");
  state.stale = true;
  assert.equal(executionBlockReason(request, now), "");
  assert.equal(requestDisplayState(request, now), "unknown");
  assert.equal(entryState(blockedEntry, now), "unknown");
  state.stale = false;
  const expired = { ...request, liveConfirmedAt: new Date(now - 15001).toISOString() };
  assert.equal(requestDisplayState(expired, now), "unknown");
  assert.equal(requestDisplayState({ ...expired, executionBlockedReason: null, executionBlockedAt: null }, now), "unknown", "An expired backend projection that cleared the block marker must not revert to Running");
  state.summary.currentRequest = expired;
  assert.equal(entryState(blockedEntry, now), "unknown");
  state.summary.currentRequest = { ...request, requestId: "request-other", entryId: "other" };
  assert.equal(entryState(blockedEntry, now), "unknown");
  state.summary.currentRequest = request;
  assert.equal(requestDisplayState({ ...request, executionBlockedAt: null }, now), "unknown");
  assert.match(app, /const value = requestState\(request\);\s+const displayValue = requestDisplayState\(request\)/);
  assert.match(app, /if \(\["running", "starting", "stopping"\]\.includes\(value\)\) \{\s+const stop =/);
  assert.match(app, /state\.projectionTimer = setInterval\(refreshRuntimeProjection, 1000\)/, "The visible projection must expire even while a refresh request is pending");
});

test("catalog filters use recorded state and never search report bodies", () => {
  const { state, filteredEntries } = helpers();
  state.entries = [
    { entryId: "a", displayName: "Alpha", description: "Decision tool", archived: false, kind: "product", executionSummary: { state: "idle" }, hiddenReport: "needle" },
    { entryId: "b", displayName: "Beta", description: "Text tool", archived: false, kind: "product", executionSummary: { state: "queued" } },
    { entryId: "c", displayName: "Archive", archived: true, kind: "product", executionSummary: { state: "ended" } },
    { entryId: "d", displayName: "Explore", archived: false, kind: "exploration", executionSummary: { state: "unknown" } },
    { entryId: "e", displayName: "Reference", archived: false, kind: "reference", executionSummary: { state: "idle" }, capabilities: { execute: false } },
  ];
  state.filter = "all"; state.query = "needle";
  assert.equal(filteredEntries().length, 0);
  state.query = ""; assert.deepEqual(Array.from(filteredEntries(), (entry) => entry.entryId), ["a", "b", "d"]);
  state.filter = "queued"; assert.deepEqual(Array.from(filteredEntries(), (entry) => entry.entryId), ["b"]);
  state.filter = "attention"; assert.deepEqual(Array.from(filteredEntries(), (entry) => entry.entryId), ["d"]);
  state.filter = "archived"; assert.deepEqual(Array.from(filteredEntries(), (entry) => entry.entryId), ["c"]);
  state.filter = "exploration"; assert.deepEqual(Array.from(filteredEntries(), (entry) => entry.entryId), ["d"]);
  state.filter = "reference"; assert.deepEqual(Array.from(filteredEntries(), (entry) => entry.entryId), ["e"]);
});

test("unfiltered catalog without formed products points to explorations", () => {
  const { state, emptyListState } = helpers();
  state.entries = [{ entryId: "explore", kind: "exploration", archived: false }]; state.filter = "all"; state.query = "";
  assert.deepEqual({ ...emptyListState([]) }, { messageKey: "noFormedProducts", actionKey: "viewExplorations", target: "exploration" });
  state.query = "missing";
  assert.deepEqual({ ...emptyListState([]) }, { messageKey: "noMatches", actionKey: "clearFilters", target: "all" });
});

test("product detail trusts only the confirmed matching center request", () => {
  const { state, scopedCenterRuntimeState, runtimeStateValue, runtimeLabel, centerRuntimeContextValue } = journalHelpers();
  const now = Date.now();
  const request = { requestId: "request-a", entryId: "entry-a", state: "running", liveConfirmedAt: new Date(now - 1000).toISOString() };
  state.data = { entry: { entryId: "entry-a", executionSummary: { requestId: "request-a", state: "running" } }, cycles: [{ status: "completed", active: false }] };
  state.centerSummary = { currentRequest: request };
  state.statusFailed = false;
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), "running");
  assert.equal(runtimeStateValue(), "running");
  assert.equal(runtimeLabel(), "Running");
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "Current work · Running");
  state.centerSummary = { currentRequest: { ...request, entryId: "entry-b" } };
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), null);
  assert.equal(runtimeStateValue(), "unknown");
  assert.equal(runtimeLabel(), "Status unconfirmed");
  state.centerSummary = { currentRequest: { ...request, liveConfirmedAt: null } };
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), null);
});

test("product detail drops stale or disconnected running evidence", () => {
  const { state, freshCenterRequest, scopedCenterRuntimeState, runtimeStateValue, runtimeLabel, centerRuntimeContextValue } = journalHelpers();
  const now = Date.now();
  const entry = { entryId: "entry-a", executionSummary: { requestId: "request-a", state: "running" } };
  const currentRequest = { requestId: "request-a", entryId: "entry-a", state: "running", liveConfirmedAt: new Date(now - 1000).toISOString() };
  state.data = { entry, runtime: { state: "running" } }; state.centerSummary = { currentRequest }; state.statusFailed = true;
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), null);
  assert.equal(runtimeStateValue(), "unknown");
  assert.equal(runtimeLabel(), "Status unconfirmed");
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "");
  state.statusFailed = false; state.centerSummary.currentRequest.liveConfirmedAt = new Date(now - 15001).toISOString();
  assert.equal(freshCenterRequest(state.centerSummary, now), null);
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), null);
  assert.equal(runtimeStateValue(), "unknown");
  assert.equal(runtimeLabel(), "Status unconfirmed");
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "");
});

test("product detail labels recorded request states without claiming product completion", () => {
  const { state, scopedRecordedRuntimeState, runtimeStateValue, runtimeStatusLabel } = journalHelpers();
  state.statusFailed = false; state.centerSummary = { currentRequest: null };
  const labels = { ended: "Ended", canceled: "Work canceled", failed: "Work failed", queued: "Work queued", attention: "Work needs review" };
  for (const [value, label] of Object.entries(labels)) {
    state.data = { entry: { entryId: "entry-a", executionSummary: { requestId: `request-${value}`, state: value } } };
    assert.equal(scopedRecordedRuntimeState(), value);
    assert.equal(runtimeStateValue(), value);
    assert.equal(runtimeStatusLabel(value), label);
    assert.doesNotMatch(label, /product|complete/i);
  }
  state.data = { entry: { entryId: "entry-a", executionSummary: { state: "ended" } } };
  assert.equal(scopedRecordedRuntimeState(), null);
  assert.equal(runtimeStateValue(), "unknown");
});

test("cross-product running context includes the queued-plan identity", () => {
  const { state, requestContextLabel, centerRuntimeContextValue } = journalHelpers();
  assert.equal(requestContextLabel({ displayName: "Autonomous Company", config: { model: "gpt-5.6-luna", effort: "high" } }), "Autonomous Company · gpt-5.6-luna · high");
  assert.equal(requestContextLabel({ displayName: "Autonomous Company", sourceId: "source_1234567890" }), "Autonomous Company · …34567890");
  const now = Date.now(); state.statusFailed = false;
  state.centerSummary = { currentRequest: { requestId: "other", entryId: "entry-b", state: "starting", liveConfirmedAt: new Date(now - 1000).toISOString(), displayName: "Autonomous Company", config: { model: "gpt-5.6-luna", effort: "high" } } };
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "Other work · Starting: Autonomous Company · gpt-5.6-luna · high");
  state.centerSummary.currentRequest.state = "stopping";
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "Other work · Stopping: Autonomous Company · gpt-5.6-luna · high");
});

test("product detail shows only fresh matching unresolved-P1 protection", () => {
  const { state, centerRequestDisplayState, scopedCenterRuntimeState, runtimeStateValue, runtimeLabel, centerRuntimeContextValue } = journalHelpers();
  const now = Date.now();
  const request = { requestId: "request-p1", entryId: "entry-a", state: "running", liveConfirmedAt: new Date(now - 1000).toISOString(), executionBlockedReason: "unresolved_p1", executionBlockedAt: new Date(now - 2000).toISOString(), displayName: "Guarded product", config: { model: "gpt-6-sol", effort: "high" } };
  state.statusFailed = false;
  state.data = { entry: { entryId: "entry-a", executionSummary: { requestId: "request-p1", state: "blocked", reason: "unresolved_p1" } } };
  state.centerSummary = { currentRequest: request };
  assert.equal(centerRequestDisplayState(request, now), "blocked");
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), "blocked");
  assert.equal(runtimeStateValue(), "blocked");
  assert.equal(runtimeLabel(), "Protection paused · Waiting for human review");
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "Current work · Needs attention");
  state.centerSummary = { currentRequest: { ...request, entryId: "entry-b" } };
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "Other work · Needs attention: Guarded product · gpt-6-sol · high");
  state.centerSummary = { currentRequest: { ...request, liveConfirmedAt: new Date(now - 15001).toISOString() } };
  assert.equal(scopedCenterRuntimeState(state.data, state.centerSummary, now), null);
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "");
  state.centerSummary = { currentRequest: request }; state.statusFailed = true;
  assert.equal(runtimeStateValue(), "unknown");
  assert.equal(centerRuntimeContextValue(state.centerSummary, now), "");
});

test("linked exploration and product cycles stay in one default paginated history", async () => {
  const { context, fetchFullScopedJournal, historyGroups } = journalHelpers();
  const product = { id: "product-1", identityKind: "product", number: 1, sequenceNumber: 3, status: "completed" };
  const explorations = [2, 1].map(number => ({ id: `exp-${number}`, identityKind: "exploration", number, sequenceNumber: number, status: "completed" }));
  const envelope = { entryId: "entry-a", sourceId: "source-a", sourceRevision: 7, total: 3 };
  const pages = [{ ...envelope, cycles: [product], nextBefore: "cursor-a" }, { ...envelope, cycles: explorations, nextBefore: null }];
  const requests = [];
  context.fetch = async url => { requests.push(url); return { ok: true, json: async () => ({ schemaVersion: 1, data: pages.shift() }) }; };
  const result = await fetchFullScopedJournal();
  assert.deepEqual(Array.from(result.cycles, cycle => cycle.id), ["product-1", "exp-2", "exp-1"]);
  assert.deepEqual(Array.from(result.cycles, cycle => cycle.sequenceNumber), [3, 2, 1]);
  assert.deepEqual(Array.from(historyGroups(result, product).main, cycle => cycle.id), ["exp-2", "exp-1"]);
  assert.equal(result.cycles[0].number, 1, "Display numbering must not replace the product cycle number");
  assert.match(requests[1], /before=cursor-a&sourceId=source-a/);
  assert.ok(requests.every(url => !url.includes("section=")), "The default API supplies the full linked history");
});

test("continuous history rejects switched sources, revisions, duplicate cycles and incomplete pages", async () => {
  const envelope = { entryId: "entry-a", sourceId: "source-a", sourceRevision: 7, total: 2 };
  const first = { ...envelope, cycles: [{ id: "product-1" }], nextBefore: "cursor-a" };
  const second = { ...envelope, cycles: [{ id: "exp-1" }], nextBefore: null };
  for (const [change, error] of [
    [{ entryId: "entry-b" }, /Journal source changed/],
    [{ sourceId: "source-b" }, /Journal source changed/],
    [{ sourceRevision: 8 }, /Journal source changed/],
    [{ cycles: [{ id: "product-1" }] }, /Repeated journal cycle/],
    [{ cycles: [] }, /Incomplete journal history/],
    [{ nextBefore: "cursor-a" }, /Repeated journal cursor/],
  ]) {
    const { context, fetchFullScopedJournal } = journalHelpers();
    const pages = [first, { ...second, ...change }];
    context.fetch = async () => ({ ok: true, json: async () => ({ schemaVersion: 1, data: pages.shift() }) });
    await assert.rejects(fetchFullScopedJournal(), error);
  }
});

test("standalone exploration keeps its own cycles in the main journal", () => {
  const { historyGroups } = journalHelpers();
  const data = { entry: { kind: "exploration" }, cycles: [{ id: "exp-2", identityKind: "exploration" }, { id: "exp-1", identityKind: "exploration" }] };
  assert.deepEqual(Array.from(historyGroups(data, data.cycles[0]).main, cycle => cycle.id), ["exp-1"]);
});

test("shared idle label describes a live loop waiting for its next cycle", () => {
  const { context, state, runtimeStatusLabel } = journalHelpers();
  state.language = "zh-CN";
  assert.equal(runtimeStatusLabel("idle"), "等待下一轮");
  state.language = "en";
  assert.equal(runtimeStatusLabel("idle"), "Waiting for next cycle");
  assert.equal(context.window.DashboardStatus.visual("idle"), "pending");
});

test("center actions use the versioned envelope routes and explicit write preconditions", () => {
  for (const route of ["/summary", "/entries?filter=all&sort=activity&limit=100", "/requests?limit=100", "/operations", "/imports/probe", "/imports/commit", "/explorations", "/queue/order", "/queue/stop-all", "/preferences"]) {
    assert.ok(app.includes(route), `Missing route ${route}`);
  }
  assert.match(app, /expectedSourceRevision: entry\.sourceRevision/);
  assert.match(app, /expectedDispatchId: request\.dispatchId/);
  assert.match(app, /expectedRevision: state\.summary\?\.queueRevision/);
  assert.match(app, /kindHint: "reference"/);
  assert.match(app, /mode: form\.elements\.mode\.value === "reference" \? "reference" : "readonly"/);
  assert.match(app, /entry\.kind !== "reference"/);
  assert.match(app, /\/entries\/\$\{encodeURIComponent\(entry\.entryId\)\}\/detach/);
  assert.match(app, /source\.displayName \|\| source\.rootName/);
  assert.match(app, /source\.displayPath/);
  assert.match(app, /X-Idempotency-Key/);
});

test("uncertain transport retries reuse an intent key until success", async () => {
  const { write, context } = helpers(); const requests = []; let call = 0;
  context.fetch = async (_url, options) => {
    requests.push(JSON.parse(options.body)); call += 1;
    if (call <= 2) throw new TypeError("transport lost");
    return { ok: true, status: 200, json: async () => ({ schemaVersion: 1, data: { accepted: true } }) };
  };
  await assert.rejects(write("/explorations", { direction: "A" }));
  await assert.rejects(write("/explorations", { direction: "B" }));
  await write("/explorations", { direction: "A" });
  await write("/explorations", { direction: "A" });
  assert.equal(requests[0].idempotencyKey, requests[2].idempotencyKey);
  assert.notEqual(requests[0].idempotencyKey, requests[1].idempotencyKey);
  assert.notEqual(requests[2].idempotencyKey, requests[3].idempotencyKey);
});

test("product detail routes are entry scoped with no standalone API fallback", () => {
  assert.match(journalHTML, /id="productSwitcherDialog"/);
  assert.match(journalApp, /\^\\\/products\\\/\(\[\^\/\]\+\)/);
  assert.match(journalApp, /fetchFullScopedJournal\(\)/);
  assert.match(journalApp, /scopedJournalPath\('\/journal'\).*limit=100/);
  assert.match(journalApp, /scopedJournalPath\('\/usage'\).*period=/);
  assert.match(journalApp, /fetchScopedText\(id === 'runtime' \? state\.data\.runtimeLogUrl : cycle\?\.logUrl/);
  assert.match(journalApp, /fetchCenter\(scopedJournalPath\('\/media\/capture'\), options/);
  assert.doesNotMatch(journalApp, /['"]\/api\/(?:journal|language|action|product-media|log-tail)(?:[/'"?])/);
  assert.ok(journalApp.includes("await Promise.all([fetchFullScopedJournal(), fetchCenter('/summary')])"));
  assert.match(journalApp, /fetchAllCenterEntries\(\)/);
  assert.match(journalApp, /engine: recordedCycle\?\.engine \|\| 'unknown'/);
  assert.match(journalApp, /reasoning: recordedCycle\?\.observedConfig\?\.reasoning \|\| 'unknown'/);
  assert.match(journalApp, /state\.data\?\.entry\?\.sourceRecordRevision/);
});

test("blank exploration direction stays a string and preparations survive refresh", () => {
  assert.match(app, /direction: text\(group\.querySelector/);
  assert.doesNotMatch(app, /direction: text\([^\n]+\|\| null/);
  assert.match(app, /state\.operations = operations\.items/);
  assert.match(app, /groups\.operationAttention/);
  assert.match(app, /preparationAttentionSection/);
});

test("owned attention dispatches retain stop controls", () => {
  const { requestOwnsDispatch } = helpers();
  assert.equal(requestOwnsDispatch({ state: "attention", dispatchId: "dispatch-a" }), true);
  assert.equal(requestOwnsDispatch({ state: "attention", dispatchId: null }), false);
  assert.equal(requestOwnsDispatch({ state: "queued", dispatchId: "dispatch-a" }), false);
  assert.match(app, /groups\.attention\.some\(requestOwnsDispatch\)/);
});

test("refreshable product and queue controls have stable focus identities", () => {
  for (const value of ["entry:${entry.entryId}:view", "entry:${entry.entryId}:continue-menu", "request:${request.requestId}:cancel", "request:${request.requestId}:stop", "queue-preview:${request.requestId}"]) {
    assert.ok(app.includes(value), `Missing stable focus key ${value}`);
  }
  assert.match(app, /const focused = rememberFocus\(\);[\s\S]*restoreFocus\(focused\)/);
});

test("preview links require exact product ownership and a separate loopback origin", () => {
  const { state, safePreviewURL } = journalHelpers();
  const id = "a".repeat(32);
  state.data = { project: { stableId: id } };
  const artifact = { kind: "preview", available: true, productId: id, url: "http://127.0.0.1:8765/" };
  assert.equal(safePreviewURL(artifact), artifact.url);
  for (const invalid of [
    { ...artifact, productId: "b".repeat(32) },
    { ...artifact, available: false },
    { ...artifact, url: "http://127.0.0.1:8843/" },
    { ...artifact, url: "https://127.0.0.1:8765/" },
    { ...artifact, url: "http://localhost:8765/" },
  ]) assert.equal(safePreviewURL(invalid), null);
});

test("journal page identity includes source revision and cycle list", () => {
  const { journalPageMatches } = journalHelpers();
  const expected = { entryId: "entry-a", sourceId: "source-a", sourceRevision: 7 };
  assert.equal(journalPageMatches({ ...expected, cycles: [] }, expected), true);
  assert.equal(journalPageMatches({ ...expected, sourceRevision: 8, cycles: [] }, expected), false);
  assert.equal(journalPageMatches({ ...expected, cycles: null }, expected), false);
});

test("limited journal rows load detail within the same source snapshot", () => {
  assert.match(journalApp, /detailStatus === 'limited'/);
  assert.match(journalApp, /scopedJournalPath\(`\/records\/\$\{encodeURIComponent\(cycleId\)\}`\)/);
  assert.match(journalApp, /expected\.token !== state\.detailToken/);
  assert.match(journalApp, /detail\?\.entryId !== expected\.entryId/);
  assert.match(journalApp, /detail\?\.sourceRevision !== expected\.sourceRevision/);
});

// Keep the production wire() listeners: helper-only tests missed these races.
function importHarness() {
  const { state, context, wire, setRenderPage } = helpers();
  function node() {
    const listeners = new Map();
    return {
      hidden: false, disabled: false, value: '', open: false, children: [], style: {}, dataset: {}, setAttribute() {}, removeAttribute() {}, closest() { return null; }, querySelectorAll() { return []; },
      classList: { toggle() {} },
      addEventListener(type, listener, options = {}) { const list = listeners.get(type) || []; list.push({ listener, once: options.once }); listeners.set(type, list); },
      emit(type) {
        const list = listeners.get(type) || []; listeners.set(type, list.filter(item => !item.once));
        let result; for (const { listener } of list) result = listener({ currentTarget: this, target: this, preventDefault() {} });
        return result;
      },
      append(...children) { this.children.push(...children); },
      replaceChildren() { this.children = []; },
      focus() {}, querySelector() { return null; },
      showModal() { this.open = true; }, close() { this.open = false; this.emit('close'); },
    };
  }
  const nodes = {};
  context.document.getElementById = id => nodes[id] ||= Object.assign(node(), { id });
  const get = context.document.getElementById;
  context.document.createElement = node;
  context.window.DashboardUI.element = (_tag, _className, text) => Object.assign(node(), { textContent: text });
  context.window.DashboardUI.notify = () => {};
  context.window.DashboardUI.alertMessage = text => Object.assign(node(), { textContent: text });
  context.document.addEventListener = () => {};
  const dialog = get('importDialog');
  const close = node(); close.closest = () => dialog;
  context.document.querySelectorAll = selector => selector === '.dialog-close' ? [close] : selector === 'dialog' ? [dialog] : [];
  context.document.querySelector = selector => selector === 'dialog[open]' && dialog.open ? dialog : null;
  get('environmentForm').elements = { candidate: node(), user: node() };
  const form = get('importForm'); const status = node();
  form.querySelector = selector => selector === '[type="submit"]' ? get('probeButton') : selector === '.form-status' ? status : null;
  const mode = [node(), node()]; mode.value = 'readonly';
  form.elements = { root: node(), mode };
  form.reset = () => { form.elements.root.value = ''; mode.value = 'readonly'; };
  const requests = [];
  context.fetch = (url, options) => new Promise((resolve, reject) => requests.push({ url, body: JSON.parse(options.body), resolve, reject }));
  context.performance = { now: () => 0 }; context.window.DashboardUI.mountControls = () => {}; wire(); get('importButton').emit('click');
  const finish = (index, error = false) => requests[index].resolve({ ok: !error, status: error ? 400 : 200,
    json: async () => error ? { code: 'SOURCE_MISSING' } : { schemaVersion: 1, data: { candidateId: `candidate-${index}`, candidateHash: `hash-${index}` } } });
  return { state, context, setRenderPage, get, form, mode, status, close, dialog, requests, finish };
}

for (const change of ['path', 'mode', 'close', 'escape']) {
  for (const error of [false, true]) {
    test(`wired import ignores late ${error ? 'error' : 'success'} after ${change}`, async () => {
      const h = importHarness();
      h.form.elements.root.value = '/a';
      const pending = h.form.emit('submit');
      assert.equal(h.get('probeButton').disabled, true);
      if (change === 'path') { h.form.elements.root.value = '/b'; h.form.elements.root.emit('input'); }
      if (change === 'mode') { h.mode.value = 'reference'; h.mode[1].emit('change'); }
      if (change === 'close') h.close.emit('click');
      if (change === 'escape') { h.dialog.emit('cancel'); h.dialog.close(); }
      if (change === 'close' || change === 'escape') h.get('importButton').emit('click');
      h.finish(0, error); await pending;
      assert.equal(h.state.probe, null);
      assert.equal(h.get('probeResult').hidden, true);
      assert.equal(h.get('commitImportButton').hidden, true);
      assert.equal(h.status.textContent, '');
      assert.equal(h.get('probeButton').disabled, false);
    });
  }
}

for (const order of [[0, 1], [1, 0]]) {
  test(`wired import keeps newer intent when probes finish ${order.join(' then ')}`, async () => {
    const h = importHarness();
    h.form.elements.root.value = '/a';
    const first = h.form.emit('submit');
    h.form.elements.root.value = '/b'; h.form.elements.root.emit('input');
    assert.equal(h.get('probeButton').disabled, false);
    const second = h.form.emit('submit');
    const promises = [first, second];
    h.finish(order[0]); await promises[order[0]];
    if (order[0] === 0) {
      assert.equal(h.get('probeButton').disabled, true);
      assert.equal(h.state.probe, null);
    }
    h.finish(order[1]); await promises[order[1]];
    assert.equal(h.state.probe.candidateId, 'candidate-1');
    assert.equal(h.get('commitImportButton').hidden, false);
    assert.equal(h.get('probeButton').disabled, false);
    assert.equal(h.requests[1].body.root, '/b');
  });
}

test('wired import invalidates a probe even when the path changes back', async () => {
  const h = importHarness(); h.form.elements.root.value = '/a';
  const pending = h.form.emit('submit');
  h.form.elements.root.value = '/b'; h.form.elements.root.emit('input');
  h.form.elements.root.value = '/a'; h.form.elements.root.emit('input');
  h.finish(0); await pending;
  assert.equal(h.state.probe, null);
  assert.equal(h.get('commitImportButton').hidden, true);
});

// Exercise actual event handlers without a browser; render-only DOM work is stubbed.
function harness() {
  class Node {
    constructor() { this.children = []; this.listeners = {}; this.dataset = {}; this.style = {}; this.disabled = false; this.open = false; this.textContent = ''; this.classList = { toggle() {}, contains() { return false; }, add() {}, remove() {} }; }
    append(...nodes) { this.children.push(...nodes); }
    replaceChildren(...nodes) { this.children = nodes; }
    addEventListener(name, handler) { this.listeners[name] = handler; }
    querySelector(selector) { if (selector === 'form' || selector === '.template-controls') return null; return this.status ||= new Node(); }
    querySelectorAll() { return []; }
    setAttribute() {} removeAttribute() {} closest() { return null; }
    reset() {}
    showModal() { this.open = true; }
    close() { this.open = false; }
    focus() {}
    fire(name) { return this.listeners[name]({ preventDefault() {}, currentTarget: this }); }
  }
  const nodes = {};
  const document = { getElementById: id => nodes[id] ||= Object.assign(new Node(), { id }), createElement: () => new Node(), querySelectorAll: () => [], querySelector: () => null, addEventListener() {} };
  document.getElementById('environmentForm').elements = { candidate: new Node(), user: new Node() };
  document.getElementById('importForm').elements = { mode: [], root: new Node() };
  const context = vm.createContext({ window: {}, document, performance: { now: () => 0 }, location: { origin: "http://127.0.0.1:8810" }, URL, Intl, Date, Number, Object, Set, Map, String, Math, AbortController,
    setTimeout: () => 1, clearTimeout() {}, crypto: { randomUUID: () => 'intent-one' } });
  context.window.DashboardNavigation = { register(_kind, mount) { mount({ document, ui: { element: (_tag, _className, text) => Object.assign(new Node(), {textContent: text}), mountControls() {}, notify() {}, alertMessage: text => Object.assign(new Node(), {textContent: text}) }, active: true, listen() {}, request: () => ({ valid: () => true, done() {} }) }); } };
  vm.runInContext(fs.readFileSync(path.join(dashboard, 'date-time.js'), 'utf8'), context);
  vm.runInContext(fs.readFileSync(path.join(dashboard, 'center-i18n.js'), 'utf8'), context);
  const app = fs.readFileSync(path.join(dashboard, 'center.js'), 'utf8');
  const end = app.lastIndexOf('\n  applyLanguage(); wire(); renderPage(); refresh();');
  vm.runInContext(app.slice(0, end) + '\n renderPage = () => {}; renderQueue = () => {}; globalThis.center = {state, wire, runRequestAction, confirmRequestAction, queueItem, refresh, api, submitProbe, commitImport, loadPreferences, savePreferences, openSourceManager, refreshSourceManager, sourceOperation, openContinue, submitContinue, submitNewWork, openDialog, setQueueObserver: callback => { openQueue = callback; }, setGroupRenderer: callback => { updateGroupButtons = callback; }};\n});', context);
  context.center.state.language = 'en';
  context.center.wire();
  nodes.confirmForm.querySelector = selector => selector === '[type="submit"]' ? document.getElementById('confirmActionButton') : nodes.confirmForm.status ||= new Node();
  nodes.importForm.querySelector = selector => selector === '[type="submit"]' ? document.getElementById('probeButton') : nodes.importForm.status ||= new Node();
  return { ...context.center, context, nodes };
}
function envelope(data, revision = 1, observedAt = '2026-09-30T10:00:00Z') {
  return { ok: true, status: 200, json: async () => ({ schemaVersion: 1, centerId: 'fixture', revision, observedAt, data }) };
}
function refreshResponse(url) {
  return envelope(url.includes('/summary') ? { language: 'en' } : url.includes('/preferences') ? {} : { items: [], total: 0 });
}
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }

test('pending request actions retain raw failure for a later propagating caller', async () => {
  const h = harness(); const pending = deferred(); let writes = 0;
  h.context.fetch = async (url, options) => options.method === 'POST' ? (++writes, pending.promise) : refreshResponse(url);
  const request = { requestId: 'request-one', revision: 1 };
  const first = h.runRequestAction(request, 'reconcile');
  const duplicate = h.runRequestAction(request, 'reconcile', true);
  const rejection = assert.rejects(duplicate, /Connection lost/);
  pending.reject(new Error('Connection lost')); await first; await rejection;
  assert.equal(writes, 1); assert.match(h.nodes.actionError.children.map(node => node.textContent).join(''), /Connection lost/);
});

test('a different pending request action cannot satisfy a new confirmation', async () => {
  const h = harness(); const pending = deferred(); let writes = 0;
  h.context.fetch = async (url, options) => options.method === 'POST' ? (++writes, pending.promise) : refreshResponse(url);
  const request = { requestId: 'request-one', revision: 1 };
  const first = h.runRequestAction(request, 'reconcile');
  await assert.rejects(h.runRequestAction(request, 'stop', true), error => error.code === 'ACTION_IN_PROGRESS');
  assert.equal(writes, 1);
  pending.resolve(envelope({})); await first;
});

for (const action of ['stop', 'cancel']) {
  for (const failure of ['transport', 'revision']) {
    test(`${action} confirmation retains ${failure} failure and suppresses repeated submit`, async () => {
      const h = harness(); const pending = deferred(); const writes = [];
      h.context.fetch = async (url, options) => { if (options.method === 'POST') { writes.push(JSON.parse(options.body)); return pending.promise; } return refreshResponse(url); };
      h.confirmRequestAction({ requestId: 'request-one', dispatchId: 'dispatch-one', revision: 7 }, action);
      const submit = h.nodes.confirmForm.fire('submit');
      const repeated = h.nodes.confirmForm.fire('submit');
      const pendingCount = writes.length; const disabled = h.nodes.confirmActionButton.disabled;
      if (failure === 'transport') pending.reject(new Error('Connection lost'));
      else pending.resolve({ ok: false, status: 409, json: async () => ({ code: 'REVISION_CONFLICT' }) });
      await Promise.all([submit, repeated]);
      assert.equal(pendingCount, 1); assert.equal(disabled, true);
      assert.equal(h.nodes.confirmDialog.open, true);
      assert.match(h.nodes.confirmForm.status.textContent, failure === 'transport' ? /Connection lost/ : /changed|refresh/i);
      assert.equal(h.nodes.confirmActionButton.disabled, false);
      h.context.fetch = async (url, options) => { if (options.method === 'POST') { writes.push(JSON.parse(options.body)); return envelope({}); } return refreshResponse(url); };
      await h.nodes.confirmForm.fire('submit');
      assert.equal(writes.length, 2); assert.equal(writes[1].idempotencyKey, writes[0].idempotencyKey);
      assert.equal(h.nodes.confirmDialog.open, false);
    });
  }
}

test('reconcile retains errors in status and blocks duplicate action across queue rerenders', async () => {
  const h = harness(); const pending = deferred(); let writes = 0;
  h.context.fetch = async () => { writes++; return pending.promise; };
  const request = { requestId: 'request-one', state: 'attention', revision: 2 };
  const buttonFor = () => h.queueItem(request, 0, 'attention', []).children.at(-1).children.at(-1);
  const button = buttonFor(); const click = button.fire('click');
  const disabled = button.disabled; const rerenderDisabled = buttonFor().disabled;
  const duplicate = button.fire('click');
  pending.reject(new Error('Connection lost')); await Promise.all([click, duplicate]);
  assert.equal(disabled, true); assert.equal(rerenderDisabled, true); assert.equal(writes, 1);
  assert.match(h.nodes.actionError.children.map(item => item.textContent).join(''), /Connection lost/); assert.equal(buttonFor().disabled, false);
});

test('refresh publishes metadata only with a complete validated snapshot, including delayed failed responses', async () => {
  const h = harness();
  h.context.fetch = async url => refreshResponse(url);
  await h.refresh();
  const original = { summary: h.state.summary, entries: h.state.entries, revision: h.state.revision, observedAt: h.state.observedAt };
  const late = deferred();
  h.context.fetch = async url => {
    if (url.includes('/operations')) throw new Error('offline');
    if (url.includes('/preferences')) return late.promise;
    return envelope(url.includes('/summary') ? { language: 'en', changed: true } : { items: [], total: 0 }, 2, '2026-09-30T11:00:00Z');
  };
  await h.refresh();
  assert.equal(h.state.stale, true);
  assert.equal(h.state.summary, original.summary); assert.equal(h.state.entries, original.entries);
  assert.equal(h.state.revision, original.revision); assert.equal(h.state.observedAt, original.observedAt);
  // A later complete refresh can succeed before the rejected batch's final reply.
  h.context.fetch = async url => envelope(url.includes('/summary') ? { language: 'en', recovered: true } : url.includes('/preferences') ? {} : { items: [], total: 0 }, 3, '2026-09-30T12:00:00Z');
  await h.refresh();
  assert.equal(h.state.stale, false); assert.equal(h.state.summary.recovered, true);
  assert.equal(h.state.revision, 3); assert.equal(h.state.observedAt, '2026-09-30T12:00:00Z');
  late.resolve(envelope({}, 2, '2026-09-30T11:00:00Z'));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(h.state.revision, 3); assert.equal(h.state.observedAt, '2026-09-30T12:00:00Z');
  assert.equal(h.state.apiRevision, 3);
});

test('invalid refresh data and failed later entry pages retain rendered metadata', async () => {
  const h = harness(); h.context.fetch = async url => refreshResponse(url); await h.refresh();
  const original = h.state.observedAt;
  for (const paginated of [false, true]) {
    h.context.fetch = async url => {
      if (url.includes('/entries')) {
        if (!paginated) return envelope({ items: null }, 4, '2026-09-30T13:00:00Z');
        if (url.includes('cursor=')) throw new Error('second page offline');
        return envelope({ items: [], nextCursor: 'next', total: 1 }, 4, '2026-09-30T13:00:00Z');
      }
      return envelope(url.includes('/summary') ? { language: 'en' } : { items: [] }, 4, '2026-09-30T13:00:00Z');
    };
    await h.refresh();
    assert.equal(h.state.stale, true); assert.equal(h.state.revision, 1); assert.equal(h.state.observedAt, original);
  }
});

test('probe then commit retains the latest API revision without advancing the rendered snapshot', async () => {
  const h = harness(); h.context.fetch = async url => refreshResponse(url); await h.refresh();
  const oldRead = deferred(); h.context.fetch = async () => oldRead.promise;
  const lateRead = h.api('/preferences');
  const writes = [];
  h.context.fetch = async (url, options) => {
    if (options.method !== 'POST') return refreshResponse(url);
    writes.push({ url, body: JSON.parse(options.body) });
    return envelope(url.endsWith('/probe') ? { candidateId: 'candidate', candidateHash: 'hash', items: [] } : {}, 7, '2026-09-30T13:00:00Z');
  };
  const form = h.nodes.importForm; form.elements.mode.value = 'readonly'; form.elements.root.value = '/fixture';
  h.nodes.importDialog.showModal();
  await form.fire('submit');
  assert.equal(h.state.probe.candidateId, 'candidate');
  assert.equal(h.state.apiRevision, 7); assert.equal(h.state.revision, 1);
  assert.equal(h.state.observedAt, '2026-09-30T10:00:00Z');
  oldRead.resolve(envelope({}, 2)); await lateRead;
  assert.equal(h.state.apiRevision, 7);
  await h.nodes.commitImportButton.fire('click');
  assert.equal(writes.length, 2); assert.equal(writes[1].body.expectedRevision, 7);
});

 test('API revision can restart when the API identifies a different center', async () => {
  const h = harness(); h.context.fetch = async () => envelope({}, 9); await h.api('/preferences');
  h.context.fetch = async () => ({ ok: true, status: 200, json: async () => ({ schemaVersion: 1, centerId: 'replacement', revision: 1, data: {} }) });
  await h.api('/preferences');
  assert.equal(h.state.apiRevision, 1); assert.equal(h.state.apiCenterId, 'replacement');
});


// Shared Radix focus behavior is exercised in the browser suite.
function preferencesHarness() {
  const h = harness();
  const form = h.nodes.settingsForm;
  form.elements = Object.fromEntries(['language', 'engine', 'model', 'effort', 'productLanguage'].map(name => [name, { value: '' }]));
  const button = { disabled: false, dataset: {}, textContent: '' }; const status = { textContent: '', classList: { toggle() {} } };
  form.querySelector = selector => selector === '[type="submit"]' ? button : selector === '.template-controls' ? null : selector === '.form-status' ? status : form.elements[selector.match(/name="([^"]+)/)?.[1]] || null;
  h.context.document.getElementById('settingsDialog').open = true;
  return { ...h, form, button, status };
}

test('preferences save uses the revision loaded into the form despite background refresh', async () => {
  const h = preferencesHarness();
  h.context.fetch = async () => envelope({ revision: 3, language: 'en', model: 'original' });
  await h.loadPreferences();
  h.context.fetch = async url => url.includes('/preferences') ? envelope({ revision: 4, language: 'en', model: 'another-window' }) : refreshResponse(url);
  await h.refresh();
  assert.equal(h.form.elements.model.value, 'original');
  const writes = [];
  h.context.fetch = async (url, options) => {
    if (options.method === 'POST') { writes.push(JSON.parse(options.body)); return { ok: false, status: 409, json: async () => ({ code: 'REVISION_CONFLICT' }) }; }
    return refreshResponse(url);
  };
  await h.savePreferences({ preventDefault() {}, currentTarget: h.form });
  assert.equal(writes[0].expectedRevision, 3, 'The revision must describe the displayed form, not the latest background read');
  assert.equal(h.nodes.settingsDialog.open, true);
});

test('preferences cannot save before a successful form load', async () => {
  const h = preferencesHarness(); const pending = deferred(); let writes = 0;
  h.context.fetch = async (url, options) => { if (options.method === 'POST') writes += 1; return pending.promise; };
  const loading = h.loadPreferences();
  assert.equal(h.button.disabled, true);
  await h.savePreferences({ preventDefault() {}, currentTarget: h.form });
  assert.equal(writes, 0);
  pending.reject(new Error('offline')); await loading;
  assert.equal(h.button.disabled, true);
});

test('preferences loading makes previously rendered template controls unreachable through failure', async () => {
  const h = preferencesHarness(); const pending = deferred(); const templates = { hidden: false };
  const query = h.form.querySelector;
  h.form.querySelector = selector => selector === '.template-controls' ? templates : query(selector);
  h.context.fetch = async () => pending.promise;
  const loading = h.loadPreferences();
  assert.equal(templates.hidden, true);
  assert.equal(h.form.elements.model.disabled, true);
  pending.reject(new Error('offline')); await loading;
  assert.equal(templates.hidden, true); assert.equal(h.button.disabled, true);
});

test('reopened preferences keep newer form data when an earlier load finishes late', async () => {
  const h = preferencesHarness(); const pending = deferred();
  h.context.fetch = async () => pending.promise;
  const first = h.loadPreferences();
  h.context.fetch = async () => envelope({ revision: 4, language: 'en', model: 'newer' });
  await h.loadPreferences();
  h.form.elements.model.value = 'my edit';
  pending.resolve(envelope({ revision: 3, language: 'en', model: 'old' })); await first;
  assert.equal(h.form.elements.model.value, 'my edit');
  assert.equal(h.state.preferences.revision, 4);
});

for (const failure of [false, true]) {
  test(`preferences late save ${failure ? 'failure' : 'success'} leaves a reopened form alone`, async () => {
    const h = preferencesHarness(); const pending = deferred(); let writes = 0;
    h.context.fetch = async () => envelope({ revision: 3, language: 'en', model: 'original' });
    await h.loadPreferences();
    h.context.fetch = async (url, options) => { if (options.method === 'POST') { writes += 1; return pending.promise; } return refreshResponse(url); };
    const saving = h.savePreferences({ preventDefault() {}, currentTarget: h.form });
    await h.savePreferences({ preventDefault() {}, currentTarget: h.form });
    assert.equal(writes, 1, 'Repeated submit must not send another write');
    h.context.fetch = async url => url.includes('/preferences') ? envelope({ revision: 4, language: 'en', model: 'newer' }) : refreshResponse(url);
    await h.loadPreferences(); h.form.elements.model.value = 'new edit';
    if (failure) pending.reject(new Error('offline')); else pending.resolve(envelope({ revision: 4, language: 'en', model: 'original' }));
    await saving;
    assert.equal(h.nodes.settingsDialog.open, true);
    assert.equal(h.form.elements.model.value, 'new edit');
    assert.equal(h.status.textContent, '');
    assert.equal(h.button.disabled, false);
  });
}

for (const action of ['refresh', 'operation']) {
  for (const failure of [false, true]) {
    test(`source manager ignores stale ${action} ${failure ? 'failure' : 'success'} after opening another product`, async () => {
      const h = harness(); const pending = deferred();
      h.context.fetch = async () => envelope({ entryId: 'entry-a', sourceId: 'source-a', displayName: 'A', sources: [] });
      await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
      h.context.fetch = async () => pending.promise;
      const first = action === 'refresh' ? h.refreshSourceManager('managementComplete') : h.sourceOperation('/sources/source-a/takeover', { expectedRevision: 1 });
      h.context.fetch = async () => envelope({ entryId: 'entry-b', sourceId: 'source-b', displayName: 'B', sources: [] });
      await h.openSourceManager({ entryId: 'entry-b', displayName: 'B' });
      let refreshes = 0; h.context.fetch = async url => { if (url.includes('/summary')) refreshes += 1; return refreshResponse(url); };
      if (failure) pending.reject(new Error('A failed')); else pending.resolve(envelope(action === 'refresh' ? { entryId: 'entry-a', sourceId: 'source-a', sources: [] } : { state: 'succeeded' }));
      await first.catch(() => {});
      assert.equal(h.state.managementEntry.entryId, 'entry-b');
      assert.equal(h.state.selectedSourceId, 'source-b');
      assert.equal(h.nodes.sourceProduct.textContent, 'B');
      if (!failure) assert.equal(refreshes, 1, 'A completed mutation must reconcile the global catalog');
      assert.equal(h.nodes.sourceManagerStatus.textContent, '', 'A must not place success or error status in B');
    });
  }
}

for (const change of ['close', 'reopen', 'selection']) {
  test(`source refresh preserves intent after ${change}`, async () => {
    const h = harness(); const pending = deferred();
    const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [] };
    h.context.fetch = async () => envelope(detail);
    await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
    h.context.fetch = async () => pending.promise;
    const first = h.refreshSourceManager('managementComplete');
    if (change === 'close') h.nodes.sourceDialog.close();
    if (change === 'selection') h.state.selectedSourceId = 'source-b';
    if (change === 'reopen') {
      h.context.fetch = async () => envelope({ ...detail, sourceId: 'source-b' });
      await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
    }
    const selected = h.state.selectedSourceId;
    h.context.fetch = async url => refreshResponse(url);
    pending.resolve(envelope(detail)); await first;
    assert.equal(h.state.selectedSourceId, selected);
    assert.equal(h.nodes.sourceManagerStatus.textContent, '');
  });
}

test('current source operation still refreshes its detail and reports success', async () => {
  const h = harness(); const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [] };
  h.context.fetch = async () => envelope(detail);
  await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
  let writes = 0;
  h.context.fetch = async (url, options) => {
    if (options.method === 'POST') { writes += 1; return envelope({ state: 'succeeded' }); }
    return url.endsWith('/entries/entry-a') ? envelope({ ...detail, revision: 2 }) : refreshResponse(url);
  };
  await h.sourceOperation('/sources/source-a/takeover', { expectedRevision: 1 });
  assert.equal(writes, 1);
  assert.equal(h.state.managementEntry.revision, 2);
  assert.equal(h.nodes.sourceManagerStatus.textContent, 'Operation completed.');
});

test('source selection away and back invalidates an older pending detail refresh', async () => {
  const h = harness(); const pending = deferred();
  const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [
    { sourceId: 'source-a', kind: 'product', revision: 1 }, { sourceId: 'source-b', kind: 'product', revision: 1 },
  ] };
  h.context.fetch = async () => envelope(detail);
  await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
  h.context.fetch = async () => pending.promise;
  const first = h.refreshSourceManager('managementComplete');
  const radios = () => h.nodes.sourceManagerBody.children[0].children.slice(1).map(label => label.children[0]);
  radios()[1].fire('change'); radios()[0].fire('change');
  h.context.fetch = async url => refreshResponse(url);
  pending.resolve(envelope({ ...detail, revision: 2 })); await first;
  assert.equal(h.state.managementEntry.revision, undefined);
  assert.equal(h.nodes.sourceManagerStatus.textContent, '');
});

test('source detail refreshes do not overwrite a newer response in the same dialog', async () => {
  const h = harness(); const first = deferred(); const second = deferred();
  const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [], revision: 1 };
  h.context.fetch = async () => envelope(detail);
  await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
  h.context.fetch = async () => first.promise; const older = h.refreshSourceManager('managementComplete');
  h.context.fetch = async () => second.promise; const newer = h.refreshSourceManager('managementComplete');
  h.context.fetch = async url => refreshResponse(url);
  second.resolve(envelope({ ...detail, revision: 3 })); await newer;
  first.resolve(envelope({ ...detail, revision: 2 })); await older;
  assert.equal(h.state.managementEntry.revision, 3);
});

for (const change of ['path', 'path-back', 'selection', 'close']) {
  test(`reconnect does not commit an obsolete probe after ${change}`, async () => {
    const h = harness(); const pending = deferred(); const writes = [];
    const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [
      { sourceId: 'source-a', kind: 'product', revision: 1 }, { sourceId: 'source-b', kind: 'product', revision: 1 },
    ] };
    h.context.fetch = async () => envelope(detail);
    await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
    const children = h.nodes.sourceManagerBody.children;
    const root = children[2].children[1]; root.value = '/a';
    const button = children[3].children[1].children[0];
    h.context.fetch = async (url, options) => { writes.push(url); return pending.promise; };
    const operation = button.fire('click');
    if (change.startsWith('path')) { root.value = '/b'; root.fire('input'); }
    if (change === 'path-back') { root.value = '/a'; root.fire('input'); }
    if (change === 'selection') children[0].children[2].children[0].fire('change');
    if (change === 'close') h.nodes.sourceDialog.close();
    pending.resolve(envelope({ candidateId: 'candidate-a', candidateHash: 'hash-a' })); await operation;
    assert.deepEqual(writes, ['/api/center/v1/imports/probe']);
    if (change.startsWith('path')) assert.equal(h.nodes.sourceManagerStatus.textContent, '', 'An invalidated probe must not leave a pending status');
  });
}

test('editing a reconnect path preserves a newer source operation status', async () => {
  const h = harness(); const probe = deferred(); const takeover = deferred();
  const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [{ sourceId: 'source-a', kind: 'product', revision: 1 }] };
  h.context.fetch = async () => envelope(detail);
  await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
  const children = h.nodes.sourceManagerBody.children; const root = children[2].children[1]; root.value = '/a';
  h.context.fetch = async url => url.endsWith('/probe') ? probe.promise : takeover.promise;
  const reconnecting = children[3].children[1].children[0].fire('click');
  const takingOver = h.sourceOperation('/sources/source-a/takeover', { expectedRevision: 1 });
  const currentStatus = h.nodes.sourceManagerStatus.textContent;
  assert.match(currentStatus, /Operation in progress/);
  root.value = '/b'; root.fire('input');
  assert.equal(h.nodes.sourceManagerStatus.textContent, currentStatus);
  probe.resolve(envelope({ candidateId: 'candidate-a', candidateHash: 'hash-a' })); await reconnecting;
  assert.equal(h.nodes.sourceManagerStatus.textContent, currentStatus);
  takeover.reject(new Error('takeover failed')); await takingOver;
  assert.match(h.nodes.sourceManagerStatus.textContent, /takeover failed/);
});

test('current reconnect preserves source identity and revision in its commit', async () => {
  const h = harness(); const writes = [];
  const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [{ sourceId: 'source-a', kind: 'product', revision: 7 }] };
  h.context.fetch = async () => envelope(detail);
  await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
  const children = h.nodes.sourceManagerBody.children;
  children[2].children[1].value = '/a';
  h.context.fetch = async (url, options) => {
    if (options.method === 'POST') {
      writes.push({ url, body: JSON.parse(options.body) });
      return envelope(url.endsWith('/probe') ? { candidateId: 'candidate-a', candidateHash: 'hash-a' } : {});
    }
    return url.endsWith('/entries/entry-a') ? envelope(detail) : refreshResponse(url);
  };
  await children[3].children[1].children[0].fire('click');
  assert.equal(writes.length, 2);
  assert.equal(writes[1].url, '/api/center/v1/sources/source-a/reconnect');
  assert.equal(writes[1].body.expectedRevision, 7);
  assert.equal(writes[1].body.candidateId, 'candidate-a');
  assert.equal(h.nodes.sourceManagerStatus.textContent, 'Source reconnected.');
});

for (const superseded of [false, true]) {
  test(`source detail failure ${superseded ? 'cannot replace newer success' : 'still reports for the current request'}`, async () => {
    const h = harness(); const oldDetail = deferred(); const entered = deferred();
    const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [], revision: 1 };
    h.context.fetch = async () => envelope(detail);
    await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
    h.context.fetch = async (url, options) => {
      if (options.method === 'POST') return envelope({ state: 'succeeded' });
      entered.resolve(); return oldDetail.promise;
    };
    const older = h.sourceOperation('/sources/source-a/takeover', { expectedRevision: 1 });
    await entered.promise;
    let refreshes = 0;
    h.context.fetch = async url => {
      if (url.includes('/summary')) refreshes += 1;
      return url.endsWith('/entries/entry-a') ? envelope({ ...detail, revision: 3 }) : refreshResponse(url);
    };
    if (superseded) await h.refreshSourceManager('managementComplete');
    oldDetail.reject(new Error('detail failed')); await older;
    assert.equal(h.state.managementEntry.revision, superseded ? 3 : 1);
    assert.equal(h.nodes.sourceManagerStatus.textContent, superseded ? 'Operation completed.' : 'Action did not complete: detail failed');
    assert.equal(refreshes, superseded ? 2 : 1, 'A failed detail read must still reconcile the completed mutation globally');
  });
}

function workFormHarness(kind) {
  const h = harness();
  let transport;
  Object.defineProperty(h.context, 'fetch', { configurable: true, get: () => (url, options) => url.endsWith('/preflight')
    ? Promise.resolve(envelope({ ready: true, checks: [], environmentRevision: 0 })) : transport(url, options), set: value => { transport = value; } });
  h.context.window.DashboardIcons = { hydrate() {} };

  const form = h.nodes[kind === 'continue' ? 'continueForm' : 'newWorkForm'];
  const dialog = h.context.document.getElementById(kind === 'continue' ? 'continueDialog' : 'newWorkDialog');
  const button = { disabled: false, dataset: {}, textContent: '' }; const status = { textContent: '', classList: { toggle() {} } };
  form.elements = Object.fromEntries(['engine', 'model', 'effort', 'productLanguage', 'direction', 'executionMode'].map(name => [name, { value: '' }]));
  dialog.querySelector = selector => selector === 'form' ? form : null;
  form.reset = () => { for (const field of Object.values(form.elements)) field.value = ''; };
  form.querySelector = selector => selector === '[type="submit"]' ? button : selector === '.form-status' ? status : null;
  let queueOpens = 0; h.setQueueObserver(() => { queueOpens += 1; });
  h.context.document.querySelector = selector => selector === 'dialog[open]' ? Object.values(h.nodes).find(node => node.open) || null : null;
  h.state.stale = false;
  const group = { id: 'work-group-fixture', querySelector: selector => form.elements[selector.match(/name="([^"]+)/)?.[1]] || null };
  form.elements.count = { value: '1' };
  form.querySelectorAll = selector => selector === '.work-group' && kind === 'new' ? [group] : [];
  form.querySelector = selector => selector === '[type="submit"]' ? button : selector === '.form-status' ? status : form.elements[selector.match(/name="([^"]+)/)?.[1]] || null;
  h.setGroupRenderer(() => {});
  const open = (id = 'entry-a') => kind === 'continue'
    ? h.openContinue({ entryId: id, kind: 'product', sourceId: `source-${id}`, runtimeId: 'runtime', capabilities: { execute: true } })
    : (form.reset(), form.elements.count.value = '1', status.textContent = '', h.openDialog(dialog));
  return { ...h, form, dialog, button, status, open, queueOpens: () => queueOpens };
}

for (const kind of ['continue', 'new']) {
  for (const failure of [false, true]) {
    for (const change of ['close', 'reopen', 'new-submit']) {
      test(`${kind} work ignores old ${failure ? 'failure' : 'success'} after ${change}`, async () => {
        const h = workFormHarness(kind); h.open(); const first = deferred(); const second = deferred(); let writes = 0; let refreshes = 0;
        h.context.fetch = async (url, options) => {
          if (options.method === 'POST') { writes += 1; return writes === 1 ? first.promise : second.promise; }
          if (url.includes('/summary')) refreshes += 1;
          return refreshResponse(url);
        };
        const pending = h.form.fire('submit'); for (let i = 0; i < 20; ++i) await Promise.resolve(); h.dialog.close();
        if (change !== 'close') h.open('entry-b');
        let newer;
        if (change === 'new-submit') newer = h.form.fire('submit');
        const before = { status: h.status.textContent, disabled: h.button.disabled };
        if (failure) first.reject(new Error('old request failed')); else first.resolve(envelope({ operationId: 'operation-a' }));
        await pending;
        assert.equal(h.dialog.open, change !== 'close', 'old completion must not close the new dialog');
        assert.equal(h.status.textContent, before.status, 'old completion must not overwrite form status');
        assert.equal(h.button.disabled, before.disabled, 'old completion must not unlock a newer submission');
        assert.equal(h.queueOpens(), 0, 'old completion must not steal focus by opening the queue');
        assert.equal(refreshes, failure ? 0 : 1, 'successful writes still refresh global state');
        if (newer) { second.resolve(envelope({ operationId: 'operation-b' })); await newer; }
      });
    }
  }
}

for (const kind of ['continue', 'new']) {
  test(`${kind} work submits once and current success opens the queue`, async () => {
    const h = workFormHarness(kind); h.open(); const pending = deferred(); let writes = 0;
    h.context.fetch = async (url, options) => options.method === 'POST' ? (++writes, pending.promise) : refreshResponse(url);
    const first = h.form.fire('submit'); for (let i = 0; i < 20; ++i) await Promise.resolve(); await h.form.fire('submit');
    assert.equal(writes, 1); assert.equal(h.button.disabled, true);
    pending.resolve(envelope({ operationId: 'operation-a' })); await first;
    assert.equal(h.dialog.open, false); assert.equal(h.queueOpens(), 1);
    h.open(); assert.equal(h.button.disabled, false, 'a subsequent fresh form is usable');
  });

  test(`${kind} work current failure remains visible and permits retry`, async () => {
    const h = workFormHarness(kind); h.open(); let writes = 0;
    h.context.fetch = async (url, options) => {
      if (options.method === 'POST') { writes += 1; if (writes === 1) throw new Error('current write failed'); return envelope({}); }
      return refreshResponse(url);
    };
    await h.form.fire('submit');
    assert.equal(h.dialog.open, true); assert.match(h.status.textContent, /current write failed/); assert.equal(h.button.disabled, false);
    await h.form.fire('submit'); assert.equal(writes, 2); assert.equal(h.queueOpens(), 1);
  });

  for (const failure of [false, true]) {
    test(`${kind} work preserves edits made while ${failure ? 'failing' : 'successful'} submission waits`, async () => {
      const h = workFormHarness(kind); h.open(); const pending = deferred(); const bodies = []; let refreshes = 0;
      h.form.elements.model.value = 'submitted-model';
      h.context.fetch = async (url, options) => {
        if (options.method === 'POST') { bodies.push(JSON.parse(options.body)); return pending.promise; }
        if (url.includes('/summary')) refreshes += 1;
        return refreshResponse(url);
      };
      const first = h.form.fire('submit'); for (let i = 0; i < 20; ++i) await Promise.resolve(); h.form.elements.model.value = 'new-edit';
      if (failure) pending.reject(new Error('old fields rejected')); else pending.resolve(envelope({ operationId: 'operation-a' }));
      await first;
      assert.equal((kind === 'new' ? bodies[0].groups[0] : bodies[0]).config.model, 'submitted-model');
      assert.equal(h.form.elements.model.value, 'new-edit'); assert.equal(h.dialog.open, true);
      assert.equal(h.status.textContent, ''); assert.equal(h.button.disabled, false); assert.equal(h.queueOpens(), 0);
      assert.equal(refreshes, failure ? 0 : 1);
    });
  }

  test(`${kind} work does not open the queue over a form opened during reconciliation`, async () => {
    const h = workFormHarness(kind); h.open(); const refresh = deferred();
    h.context.fetch = async (url, options) => options.method === 'POST' ? envelope({}) : url.includes('/summary') ? refresh.promise : refreshResponse(url);
    const first = h.form.fire('submit');
    for (let i = 0; i < 30 && h.dialog.open; ++i) await Promise.resolve();
    assert.equal(h.dialog.open, false, 'the completed submitted form closed before catalog refresh');
    h.open('entry-b'); refresh.resolve(envelope({ language: 'en' })); await first;
    assert.equal(h.dialog.open, true); assert.equal(h.button.disabled, false); assert.equal(h.queueOpens(), 0);
  });
}

for (const action of ['stop', 'cancel']) {
  for (const failure of [false, true]) {
    for (const change of ['close', 'reopen', 'new-submit']) {
      test(`${action} confirmation isolates old ${failure ? 'failure' : 'success'} after ${change}`, async () => {
        const h = harness(); const first = deferred(); const second = deferred(); let writes = 0; let refreshes = 0;
        h.context.fetch = async (url, options) => {
          if (options.method === 'POST') { writes += 1; return writes === 1 ? first.promise : second.promise; }
          if (url.includes('/summary')) refreshes += 1;
          return refreshResponse(url);
        };
        h.confirmRequestAction({ requestId: 'request-a', dispatchId: 'dispatch-a', revision: 1 }, action);
        const pending = h.nodes.confirmForm.fire('submit'); h.nodes.confirmDialog.close();
        if (change !== 'close') h.confirmRequestAction({ requestId: 'request-b', dispatchId: 'dispatch-b', revision: 1 }, action);
        let newer;
        if (change === 'new-submit') {
          assert.equal(h.nodes.confirmActionButton.disabled, false, 'new confirmation must be usable while old request waits');
          newer = h.nodes.confirmForm.fire('submit');
        }
        const before = { status: h.nodes.confirmForm.status.textContent, disabled: h.nodes.confirmActionButton.disabled };
        if (failure) first.reject(new Error('old action failed')); else first.resolve(envelope({}));
        await pending;
        assert.equal(h.nodes.confirmDialog.open, change !== 'close');
        assert.equal(h.nodes.confirmForm.status.textContent, before.status, 'old error must not enter a newer confirmation');
        assert.equal(h.nodes.confirmActionButton.disabled, before.disabled, 'old finally must not unlock the new confirmation');
        assert.equal(refreshes, failure ? 0 : 1, 'successful old actions still reconcile global state');
        if (newer) { second.resolve(envelope({})); await newer; assert.equal(h.nodes.confirmDialog.open, false); }
      });
    }
  }

  test(`${action} confirmation can reopen the same pending request without duplicate writes`, async () => {
    const h = harness(); const pending = deferred(); let writes = 0;
    h.context.fetch = async (url, options) => options.method === 'POST' ? (++writes, pending.promise) : refreshResponse(url);
    const request = { requestId: 'request-a', dispatchId: 'dispatch-a', revision: 1 };
    h.confirmRequestAction(request, action); const first = h.nodes.confirmForm.fire('submit');
    h.nodes.confirmDialog.close(); h.confirmRequestAction(request, action);
    assert.equal(h.nodes.confirmActionButton.disabled, false);
    const second = h.nodes.confirmForm.fire('submit'); assert.equal(writes, 1);
    await Promise.resolve();
    assert.equal(h.nodes.confirmDialog.open, true, 'the reopened confirmation must still await the original request');
    assert.equal(h.nodes.confirmActionButton.disabled, true);
    pending.resolve(envelope({})); await Promise.all([first, second]);
    assert.equal(h.nodes.confirmDialog.open, false); assert.equal(writes, 1);
  });

  test(`${action} reopened confirmation keeps the shared request failure visible`, async () => {
    const h = harness(); const pending = deferred(); let writes = 0;
    h.context.fetch = async (url, options) => options.method === 'POST' ? (++writes, pending.promise) : refreshResponse(url);
    const request = { requestId: 'request-a', dispatchId: 'dispatch-a', revision: 1 };
    h.confirmRequestAction(request, action); const first = h.nodes.confirmForm.fire('submit');
    h.nodes.confirmDialog.close(); h.confirmRequestAction(request, action);
    const second = h.nodes.confirmForm.fire('submit'); await Promise.resolve();
    assert.equal(h.nodes.confirmDialog.open, true); assert.equal(h.nodes.confirmActionButton.disabled, true);
    pending.reject(new Error('shared operation failed')); await Promise.all([first, second]);
    assert.equal(writes, 1); assert.equal(h.nodes.confirmDialog.open, true);
    assert.equal(h.nodes.confirmActionButton.disabled, false); assert.match(h.nodes.confirmForm.status.textContent, /shared operation failed/);
  });
}

for (const [field, value] of [['language', 'zh-CN'], ['engine', 'codex'], ['model', 'new-edit'], ['effort', 'xhigh'], ['productLanguage', 'zh-CN']]) {
  test(`preferences preserve newer ${field} edits after a successful save`, async () => {
    const h = preferencesHarness(); const pending = deferred(); const writes = [];
    const original = { revision: 3, language: 'en', engine: 'claude', model: 'original', effort: 'high', productLanguage: 'en' };
    h.context.fetch = async () => envelope(original); await h.loadPreferences();
    h.context.fetch = async (url, options) => {
      if (options.method === 'POST') { writes.push(JSON.parse(options.body)); return pending.promise; }
      return url.includes('/preferences') ? envelope({ ...original, revision: 5, model: 'external-change' }) : refreshResponse(url);
    };
    const first = h.savePreferences({ preventDefault() {}, currentTarget: h.form });
    h.form.elements[field].value = value;
    pending.resolve(envelope({ ...original, revision: 4 })); await first;
    assert.equal(h.nodes.settingsDialog.open, true, 'saving old values must not close newer edits');
    assert.equal(h.form.elements[field].value, value);
    assert.equal(h.state.preferencesRevision, 4, 'the new lease is the exact successful write revision, not later polling');
    assert.equal(h.state.preferences.revision, 5, 'global preferences may update independently');
    assert.equal(h.button.disabled, false);
    assert.match(h.status.textContent, /newer edits.*not saved/i);
    assert.equal(writes[0].preferences[field], original[field], 'the completed write contains the submitted values');
    h.context.fetch = async (url, options) => {
      if (options.method === 'POST') { writes.push(JSON.parse(options.body)); return { ok: false, status: 409, json: async () => ({ code: 'REVISION_CONFLICT' }) }; }
      return refreshResponse(url);
    };
    await h.savePreferences({ preventDefault() {}, currentTarget: h.form });
    assert.equal(writes[1].expectedRevision, 4);
    assert.equal(writes[1].preferences[field], value);
    assert.equal(h.nodes.settingsDialog.open, true);
    assert.match(h.status.textContent, /changed|refresh/i);
  });
}

test('unchanged preferences still close after a successful save', async () => {
  const h = preferencesHarness(); const original = { revision: 3, language: 'en', engine: 'claude', model: 'original', effort: 'high', productLanguage: 'en' };
  h.context.fetch = async () => envelope(original); await h.loadPreferences();
  h.context.fetch = async (url, options) => options.method === 'POST' ? envelope({ ...original, revision: 4 }) : refreshResponse(url);
  await h.savePreferences({ preventDefault() {}, currentTarget: h.form });
  assert.equal(h.nodes.settingsDialog.open, false);
});

for (const failure of ['transport', 'revision', 'invalid-response']) {
  test(`preferences ${failure} failure preserves pending edits and the original revision`, async () => {
    const h = preferencesHarness(); const pending = deferred();
    h.context.fetch = async () => envelope({ revision: 3, language: 'en', model: 'original' }); await h.loadPreferences();
    h.context.fetch = async () => pending.promise;
    const saving = h.savePreferences({ preventDefault() {}, currentTarget: h.form });
    h.form.elements.model.value = 'newer-unsaved-edit';
    if (failure === 'transport') pending.reject(new Error('Connection lost'));
    else if (failure === 'revision') pending.resolve({ ok: false, status: 409, json: async () => ({ code: 'REVISION_CONFLICT' }) });
    else pending.resolve(envelope({ language: 'en', model: 'original' }));
    await saving;
    assert.equal(h.nodes.settingsDialog.open, true); assert.equal(h.form.elements.model.value, 'newer-unsaved-edit');
    assert.equal(h.state.preferencesRevision, 3); assert.equal(h.state.preferences.revision, 3);
    assert.equal(h.button.disabled, false); assert.match(h.status.textContent, /Action did not complete/);
    assert.doesNotMatch(h.status.textContent, /settings saved/i);
  });
}

for (const stage of ['load', 'save']) {
  test(`preferences ${stage} rejects malformed revision values without advancing the form lease`, async () => {
    for (const revision of [undefined, null, -1, 1.5, true, '4', Number.MAX_SAFE_INTEGER + 1, {}, []]) {
      const h = preferencesHarness();
      const original = { revision: 3, language: 'en', model: 'original' };
      if (stage === 'save') { h.context.fetch = async () => envelope(original); await h.loadPreferences(); h.form.elements.model.value = 'unsaved-edit'; }
      h.context.fetch = async () => envelope({ ...original, revision });
      if (stage === 'save') await h.savePreferences({ preventDefault() {}, currentTarget: h.form });
      else await h.loadPreferences();
      assert.equal(h.nodes.settingsDialog.open, true, `invalid revision ${JSON.stringify(revision)}`);
      assert.equal(h.state.preferencesRevision, stage === 'save' ? 3 : null);
      assert.equal(h.state.preferences?.revision ?? null, stage === 'save' ? 3 : null);
      assert.equal(h.button.disabled, stage === 'load');
      assert.match(h.status.textContent, /Action did not complete/); assert.doesNotMatch(h.status.textContent, /settings saved/i);
      if (stage === 'save') assert.equal(h.form.elements.model.value, 'unsaved-edit');
    }
  });

  test(`preferences ${stage} accepts zero and positive safe integer revisions`, async () => {
    for (const revision of [0, 4]) {
      const h = preferencesHarness(); const preferences = { revision, language: 'en', model: 'original' };
      h.context.fetch = async () => envelope(preferences); await h.loadPreferences();
      if (stage === 'save') {
        const pending = deferred();
        h.context.fetch = async (url, options) => options.method === 'POST' ? pending.promise : refreshResponse(url);
        const saving = h.savePreferences({ preventDefault() {}, currentTarget: h.form });
        h.form.elements.model.value = 'newer-edit'; pending.resolve(envelope(preferences)); await saving;
      }
      assert.equal(h.state.preferencesRevision, revision); assert.equal(h.button.disabled, false); assert.equal(h.nodes.settingsDialog.open, true);
      if (stage === 'save') assert.match(h.status.textContent, /newer edits.*not saved/i);
      else assert.equal(h.status.textContent, '');
    }
  });
}

for (const failure of [false, true]) {
  for (const change of ['path', 'mode', 'close', 'reopen', 'new-commit']) {
    test(`wired import commit isolates old ${failure ? 'failure' : 'success'} after ${change}`, async () => {
      const h = importHarness(); h.context.setTimeout = () => 1; h.context.clearTimeout = () => {}; h.setRenderPage(() => {});
      h.form.elements.root.value = '/a'; const probing = h.form.emit('submit'); h.finish(0); await probing;
      const first = deferred(); const second = deferred(); let commits = 0; let refreshes = 0;
      h.context.fetch = async (url, options) => {
        if (url.endsWith('/imports/commit')) { commits += 1; return commits === 1 ? first.promise : second.promise; }
        if (url.endsWith('/imports/probe')) return envelope({ candidateId: 'candidate-b', candidateHash: 'hash-b' });
        if (url.includes('/summary')) refreshes += 1;
        return refreshResponse(url);
      };
      const pending = h.get('commitImportButton').emit('click');
      if (change === 'path') { h.form.elements.root.value = '/b'; h.form.elements.root.emit('input'); }
      else if (change === 'mode') { h.mode.value = 'reference'; h.mode[1].emit('change'); }
      else h.close.emit('click');
      if (change === 'reopen' || change === 'new-commit') h.get('importButton').emit('click');
      let newer;
      if (change === 'new-commit') {
        h.form.elements.root.value = '/b'; await h.form.emit('submit');
        assert.equal(h.get('commitImportButton').disabled, false, 'new candidate must be usable while old commit waits');
        newer = h.get('commitImportButton').emit('click');
      }
      const before = { probe: h.state.probe, status: h.status.textContent, disabled: h.get('commitImportButton').disabled };
      if (failure) first.reject(new Error('old import failed')); else first.resolve(envelope({}));
      await pending;
      assert.equal(h.dialog.open, change !== 'close');
      assert.equal(h.state.probe, before.probe, 'old success must not clear a newer candidate');
      assert.equal(h.status.textContent, before.status, 'old error must not replace the newer form status');
      assert.equal(h.get('commitImportButton').disabled, before.disabled, 'old finally must not unlock a newer commit');
      assert.equal(refreshes, failure ? 0 : 1, 'an accepted import still refreshes the global catalog');
      if (newer) { second.resolve(envelope({})); await newer; assert.equal(h.dialog.open, false); }
    });
  }
}

for (const failure of [false, true]) {
  test(`wired import current commit ${failure ? 'failure remains retryable' : 'success closes only its own form'}`, async () => {
    const h = importHarness(); h.context.setTimeout = () => 1; h.context.clearTimeout = () => {}; h.setRenderPage(() => {});
    h.form.elements.root.value = '/a'; const probing = h.form.emit('submit'); h.finish(0); await probing;
    const pending = deferred(); const writes = []; h.state.apiRevision = 7;
    h.context.fetch = async (url, options) => {
      if (url.endsWith('/imports/commit')) { writes.push(JSON.parse(options.body)); return pending.promise; }
      return refreshResponse(url);
    };
    const first = h.get('commitImportButton').emit('click'); await h.get('commitImportButton').emit('click');
    assert.equal(writes.length, 1); assert.equal(writes[0].candidateId, 'candidate-0'); assert.equal(writes[0].candidateHash, 'hash-0');
    assert.equal(writes[0].mode, 'readonly'); assert.equal(writes[0].expectedRevision, 7);
    if (failure) pending.reject(new Error('current import failed')); else pending.resolve(envelope({}));
    await first;
    if (failure) {
      assert.equal(h.dialog.open, true); assert.match(h.status.textContent, /current import failed/);
      assert.equal(h.get('commitImportButton').disabled, false); assert.equal(h.state.probe.candidateId, 'candidate-0');
      h.context.fetch = async (url, options) => {
        if (url.endsWith('/imports/commit')) { writes.push(JSON.parse(options.body)); return envelope({}); }
        return refreshResponse(url);
      };
      await h.get('commitImportButton').emit('click');
      assert.equal(writes.length, 2); assert.equal(writes[1].idempotencyKey, writes[0].idempotencyKey);
    }
    assert.equal(h.dialog.open, false); assert.equal(h.state.probe, null); assert.equal(h.get('commitImportButton').hidden, true);
  });
}

for (const outcome of ['success', 'failure']) {
  test(`preferences loading blocks configuration edits until ${outcome}`, async () => {
    const h = preferencesHarness(); const pending = deferred();
    const fields = Object.values(h.form.elements); const closeControl = { disabled: false }; h.form.elements.close = closeControl;
    const focus = { id: 'cancel-button' }; h.context.document.activeElement = focus;
    for (const field of fields) field.focus = () => { h.context.document.activeElement = field; };
    h.context.fetch = async () => pending.promise; const loading = h.loadPreferences();
    const editableDuringLoad = fields.filter(field => !field.disabled);
    for (const field of editableDuringLoad) field.value = 'new-input-before-response';
    if (outcome === 'success') pending.resolve(envelope({ revision: 3, language: 'en', engine: 'claude', model: 'loaded-model', effort: 'high', productLanguage: 'en' }));
    else pending.reject(new Error('load failed'));
    await loading;
    assert.equal(editableDuringLoad.length, 0, 'all configuration controls must block edits that a pending GET would replace');
    assert.equal(closeControl.disabled, false, 'closing remains available');
    assert.equal(h.context.document.activeElement, focus, 'load completion must not steal focus');
    assert.ok(fields.every(field => field.disabled === (outcome === 'failure')));
    assert.equal(h.button.disabled, outcome === 'failure');
    if (outcome === 'success') assert.equal(h.form.elements.model.value, 'loaded-model');
  });
}

for (const failure of [false, true]) {
  test(`obsolete preferences load ${failure ? 'failure' : 'success'} cannot unlock a newer pending load`, async () => {
    const h = preferencesHarness(); const old = deferred(); const current = deferred();
    h.context.fetch = async () => old.promise; const first = h.loadPreferences();
    h.context.fetch = async () => current.promise; const second = h.loadPreferences();
    if (failure) old.reject(new Error('old load failed')); else old.resolve(envelope({ revision: 3, language: 'en', model: 'old' }));
    await first;
    assert.ok(Object.values(h.form.elements).every(field => field.disabled)); assert.equal(h.button.disabled, true);
    current.resolve(envelope({ revision: 4, language: 'en', model: 'current' })); await second;
    assert.ok(Object.values(h.form.elements).every(field => field.disabled === false)); assert.equal(h.button.disabled, false);
    assert.equal(h.form.elements.model.value, 'current');
  });
}

function sourceChoice(h, id) {
  const walk = node => [node, ...(node.children || []).flatMap(walk)];
  return walk(h.nodes.sourceManagerBody).find(node => node.name === 'managedSource' && node.value === id);
}

for (const failure of [false, true]) {
  test(`source action lock stays explicit after switching sources and unlocks after old ${failure ? 'failure' : 'success'}`, async () => {
    const h = harness(); const pending = deferred(); const writes = []; let selected = false;
    const detail = { entryId: 'entry-a', sourceId: 'source-a', revision: 1, capabilities: { takeover: true }, sources: [
      { sourceId: 'source-a', kind: 'product', revision: 1 }, { sourceId: 'source-b', kind: 'product', revision: 1 },
    ] };
    h.context.fetch = async () => envelope(detail); await h.openSourceManager({ entryId: 'entry-a' });
    h.context.fetch = async (url, options) => {
      if (options.method === 'POST') {
        writes.push({ url, body: JSON.parse(options.body) });
        if (url.endsWith('/takeover')) return pending.promise;
        selected = true; return envelope({});
      }
      return url.endsWith('/entries/entry-a') ? envelope({ ...detail, sourceId: selected ? 'source-b' : 'source-a' }) : refreshResponse(url);
    };
    const action = label => h.state.sourceActions.find(item => item.button.textContent === label);
    const old = action('Take over with center').button.fire('click');
    sourceChoice(h, 'source-b').fire('change');
    const useB = action('Use selected source');
    assert.equal(useB.button.disabled, true); assert.match(useB.hint.textContent, /Operation in progress/);
    assert.equal(writes.length, 1);
    const root = h.nodes.sourceManagerBody.children[2].children[1]; root.value = '/draft-for-b'; h.context.document.activeElement = root;
    if (failure) pending.reject(new Error('Old A failed')); else pending.resolve(envelope({ state: 'succeeded' }));
    await old;
    assert.equal(h.state.selectedSourceId, 'source-b'); assert.equal(h.nodes.sourceManagerStatus.textContent, '');
    assert.equal(useB.button.disabled, false); assert.equal(useB.hint.textContent, '');
    assert.equal(action('Take over with center').button.disabled, true, 'business-disabled actions stay disabled');
    assert.equal(root.value, '/draft-for-b'); assert.equal(h.context.document.activeElement, root);
    await useB.button.fire('click');
    assert.equal(writes.length, 2); assert.equal(writes[1].body.sourceId, 'source-b');
    assert.equal(h.nodes.sourceManagerStatus.textContent, 'Current source updated.');
  });
}

for (const failure of [false, true]) {
  test(`source selection clears the old pending status even when its operation later ${failure ? 'fails' : 'succeeds'}`, async () => {
    const h = harness(); const pending = deferred();
    const detail = { entryId: 'entry-a', sourceId: 'source-a', sources: [
      { sourceId: 'source-a', kind: 'product', availability: 'available' },
      { sourceId: 'source-b', kind: 'product', availability: 'available' },
    ] };
    h.context.fetch = async () => envelope(detail); await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
    h.context.fetch = async () => pending.promise;
    const old = h.sourceOperation('/sources/source-a/takeover', { expectedRevision: 1 });
    assert.match(h.nodes.sourceManagerStatus.textContent, /Operation in progress/);
    sourceChoice(h, 'source-b').fire('change');
    const statusAfterSelection = h.nodes.sourceManagerStatus.textContent;
    h.context.fetch = async url => refreshResponse(url);
    if (failure) pending.reject(new Error('old source failed')); else pending.resolve(envelope({ state: 'succeeded' }));
    await old;
    assert.equal(h.state.selectedSourceId, 'source-b');
    assert.equal(statusAfterSelection, '', 'the new source must not inherit the old action status');
    assert.equal(h.nodes.sourceManagerStatus.textContent, '', 'an ignored old completion must not leave a permanent pending label');
  });
}

test('source selection clears an earlier source error and its error styling', async () => {
  const h = harness(); let errorStyle = false;
  h.context.document.getElementById('sourceManagerStatus').classList = { toggle(name, value) { if (name === 'error') errorStyle = value; } };
  h.context.fetch = async () => envelope({ entryId: 'entry-a', sourceId: 'source-a', sources: [
    { sourceId: 'source-a', kind: 'product', availability: 'available' },
    { sourceId: 'source-b', kind: 'product', availability: 'available' },
  ] });
  await h.openSourceManager({ entryId: 'entry-a', displayName: 'A' });
  h.context.fetch = async () => { throw new Error('source A failed'); };
  await h.sourceOperation('/sources/source-a/takeover', { expectedRevision: 1 });
  assert.match(h.nodes.sourceManagerStatus.textContent, /source A failed/); assert.equal(errorStyle, true);
  sourceChoice(h, 'source-b').fire('change');
  assert.equal(h.nodes.sourceManagerStatus.textContent, ''); assert.equal(errorStyle, false);
});
