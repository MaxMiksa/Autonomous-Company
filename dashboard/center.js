window.DashboardNavigation.register('center', (view) => {
  "use strict";

  const document = view.document;
  const UI = view.ui;
  const $ = (id) => document.getElementById(id);
  const API = "/api/center/v1";
  const OPEN_STATES = new Set(["queued", "starting", "running", "stopping", "attention", "preparing"]);
  const CATALOG_FILTERS = ["all", "running", "queued", "attention", "archived", "trash", "exploration", "reference", "read_only", "paused", "ended", "idle", "unknown", "failed", "blocked", "canceled", "preparing", "starting", "stopping"];
  const TERMINAL_STATES = new Set(["ended", "failed", "canceled"]);
  const state = {
    language: "zh-CN", revision: null, apiRevision: null, apiCenterId: null, centerId: null, observedAt: null,
    summary: null, entries: [], trash: { retentionDays: 30, revision: 1, items: [] }, requests: [], operations: [], preferences: null, preferencesRevision: null, preferencesToken: 0,
    query: "", filter: "all", loading: true, stale: false, refreshing: null,
    writeGeneration: 0, refreshGeneration: 0, environmentToken: 0, environment: null,
    refreshToken: 0, dialogToken: 0, timer: null, menuEntryId: null, historyVisible: false,
    activeEntry: null, managementEntry: null, selectedSourceId: null, sourceToken: 0, sourceRefreshToken: 0, sourceStatusToken: 0, probe: null, probeToken: 0, confirmAction: null, drawerOpen: false, pendingWrites: new Map(), projectionSignature: "", projectionTimer: null,
    activeWorkGroupId: null, nextWorkGroupId: 0, workSubmitting: false,
    lastSuccessAt: null, restoreScroll: null, focusOrder: [], announcement: "",
    actionLocks: new Set(), requestActions: new Map(), sourceActions: [],
    autoRefresh: true,
    otherExpanded: false,
    sort: "activity", sortDirection: "desc", roundFilter: "all", previewMode: "screenshot",
    readParts: new Map(), pendingParts: new Map(), stagedParts: new Map(),
  };

  const VIEW_STATE_KEY = "autonomous-company:center:view:v1";
  function migrateBrowserState(storageName, oldKey, newKey) {
    try {
      const storage = window[storageName];
      const previous = storage?.getItem(oldKey);
      if (previous !== null && previous !== undefined) {
        if (storage.getItem(newKey) !== null && storage.getItem(newKey) !== previous) {
          console.warn("Stored center preferences conflict; previous value retained for explicit recovery.");
          return;
        }
        storage.setItem(newKey, previous);
        storage.removeItem(oldKey);
      }
    } catch (_) {}
  }
  migrateBrowserState("sessionStorage", "auto-company:center:view:v1", VIEW_STATE_KEY);
  migrateBrowserState("localStorage", "auto-company:center:auto-refresh", "autonomous-company:center:auto-refresh");
  function saveView() {
    try { window.sessionStorage?.setItem(VIEW_STATE_KEY, JSON.stringify({ query: $("productSearch")?.value.trim() ?? state.query, filter: state.filter, sort: state.sort, sortDirection: state.sortDirection, roundFilter: state.roundFilter, previewMode: state.previewMode, otherExpanded: state.otherExpanded, scroll: window.scrollY || 0 })); } catch (_) {}
  }
  function loadView() {
    try { state.autoRefresh = window.localStorage?.getItem("autonomous-company:center:auto-refresh") !== "off"; } catch (_) {}
    $("centerAutoRefresh").checked = state.autoRefresh;
    try {
      const saved = JSON.parse(window.sessionStorage?.getItem(VIEW_STATE_KEY) || "null");
      if (!saved) return;
      if (typeof saved.otherExpanded === "boolean") state.otherExpanded = saved.otherExpanded;
      if (["logo", "screenshot", "none"].includes(saved.previewMode)) state.previewMode = saved.previewMode;
      if (typeof saved.query === "string") state.query = saved.query;
      if (CATALOG_FILTERS.includes(saved.filter)) state.filter = saved.filter;
      if (["activity", "name", "work", "status", "round"].includes(saved.sort)) state.sort = saved.sort;
      if (["asc", "desc"].includes(saved.sortDirection)) state.sortDirection = saved.sortDirection;
      if (["all", "completed", "running", "correcting", "validating", "closing", "recovering", "handoff", "failed", "pending", "interrupted", "completed_with_timeout", "paused", "unknown", "not_started", "startup_unconfirmed", "no_rounds"].includes(saved.roundFilter)) state.roundFilter = saved.roundFilter;
      if (Number.isFinite(saved.scroll) && saved.scroll >= 0) state.restoreScroll = saved.scroll;
      $("productSearch").value = state.query;
    } catch (_) {}
  }
  function announce(value) { const node = $("searchStatus"); if (node && value !== state.announcement) { node.textContent = value; state.announcement = value; } }

  function message(key, values = {}) {
    const dictionary = window.CENTER_MESSAGES[state.language] || window.CENTER_MESSAGES.en;
    return Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, typeof value === "number" && Number.isFinite(value) ? formatNumber(value) : String(value)), dictionary[key] || key);
  }
  function formatNumber(value) { return new Intl.NumberFormat(state.language).format(value); }

  function element(tag, className, text) {
    return UI.element(tag, className, text);
  }

  function clear(node) { node.replaceChildren(); return node; }
  function text(value) { return typeof value === "string" ? value.trim() : ""; }
  function knownNumber(value) { return Number.isFinite(value) && value >= 0; }
  function focusKey(node, value) { node.dataset.focusKey = value; return node; }
  function rememberFocus() {
    const active = document.activeElement;
    state.focusOrder = [...document.querySelectorAll("[data-focus-key]")].map(node => node.dataset.focusKey);
    return active && active !== document.body ? text(active.dataset?.focusKey) : "";
  }
  function focusControl(node) {
    if (!node || node.disabled || node.closest?.('[hidden], [inert], [aria-hidden="true"], [aria-disabled="true"]') || (node.getClientRects && !node.getClientRects().length)) return false;
    node.focus({ preventScroll: true }); return true;
  }
  function restoreFocus(key) {
    if (!key) return;
    const node = [...document.querySelectorAll("[data-focus-key]")].find((item) => item.dataset.focusKey === key);
    if (focusControl(node)) return true;
    else {
      const index = state.focusOrder.indexOf(key);
      const restored = state.focusOrder.slice(index + 1).concat(state.focusOrder.slice(0, Math.max(0, index)).reverse()).map(value => [...document.querySelectorAll("[data-focus-key]")].find(item => item.dataset.focusKey === value)).some(focusControl);
      if (!restored) focusControl($("productSearch"));
      announce(message(restored ? "focusedItemMoved" : "focusedItemSearch", { count: filteredEntries().length }));
    }
  }
  function idempotencyKey() { return globalThis.crypto?.randomUUID?.() || `center-${Date.now()}-${Math.random().toString(16).slice(2)}`; }

  class APIError extends Error {
    constructor(payload, status) {
      super(payload?.message || payload?.messageKey || `HTTP ${status}`);
      this.code = payload?.code || "UNKNOWN";
      this.messageKey = payload?.messageKey || "";
      this.params = payload?.params || {};
      this.status = status;
    }
  }

  async function api(path, options = {}, timeout = 30000, snapshot = null) {
    const controller = new AbortController();
    const request = view.request(controller, options);
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(`${API}${path}`, { cache: "no-store", ...options, signal: controller.signal });
      let payload;
      try { payload = await response.json(); }
      catch (_) { throw new APIError({ code: "INVALID_RESPONSE", messageKey: "invalidResponse" }, response.status); }
      if (!request.valid()) throw new DOMException('Inactive view', 'AbortError');
      if (!response.ok || payload?.code) throw new APIError(payload, response.status);
      if (!payload || payload.schemaVersion !== 1 || !Object.hasOwn(payload, "data")) throw new APIError({ code: "INVALID_RESPONSE", messageKey: "invalidResponse" }, response.status);
      const target = snapshot || { centerId: state.apiCenterId, revision: state.apiRevision };
      if (Number.isSafeInteger(payload.revision) && payload.revision >= 0) {
        const sameCenter = !payload.centerId || payload.centerId === target.centerId;
        if (!sameCenter || target.revision === null || payload.revision >= target.revision) {
          target.centerId = payload.centerId || target.centerId;
          target.revision = payload.revision;
          if (payload.observedAt) target.observedAt = payload.observedAt;
        }
      }
      // Partial refreshes cannot publish metadata for the data still on screen.
      if (!snapshot) { state.apiCenterId = target.centerId; state.apiRevision = target.revision; }
      return payload.data;
    } finally { clearTimeout(timer); request.done(); }
  }

  async function write(path, body, timeout = 30000) {
    const signature = `${path}\n${JSON.stringify(body)}`;
    const key = body.idempotencyKey || state.pendingWrites.get(signature) || idempotencyKey(); state.pendingWrites.set(signature, key);
    const value = { ...body, idempotencyKey: key };
    try {
      const result = await api(path, { method: "POST", headers: { "Content-Type": "application/json", "X-Idempotency-Key": key }, body: JSON.stringify(value) }, timeout);
      state.writeGeneration += 1; state.pendingWrites.delete(signature); return result;
    } catch (error) { throw error; }
  }

  function errorText(error) {
    const map = {
      SOURCE_MISSING: "sourceMissing", SOURCE_CONFLICT: "sourceConflict", SOURCE_CHANGED: "sourceChanged",
      READ_ONLY_SOURCE: "readOnlySource", CONTEXT_UNAVAILABLE: "contextUnavailable", RUNTIME_INCOMPATIBLE: "runtimeIncompatible",
      SLOT_BUSY: "slotBusy", DISPATCH_UNCERTAIN: "dispatchUncertain", STOP_UNCONFIRMED: "stopUnconfirmed",
      GOVERNANCE_PAUSED: "governancePaused", BUDGET_PAUSED: "budgetPaused", CURSOR_EXPIRED: "cursorExpired",
      REVISION_CONFLICT: "revisionConflict", UNSUPPORTED: "unsupported", INVALID_RESPONSE: "invalidResponse",
      EXECUTION_DOMAIN_UNCONFIGURED: "executionUnavailable", OPEN_REQUEST_EXISTS: "openRequestExists",
      PRODUCT_LANGUAGE_LOCKED: "productLanguageLocked", PRODUCT_REGISTRATION_INVALID: "productRegistrationInvalid", UNRESOLVED_P1: "unresolvedP1",
      RECOVERY_REQUIRED: "recoveryRequired", INVALID_CONFIG: "invalidConfig", INVALID_PREFERENCE: "invalidConfig", INVALID_TEMPLATE: "templateNameInvalid", TEMPLATE_NOT_FOUND: "selectTemplateFirst", TEMPLATE_NAME_CONFLICT: "templateNameConflict",
      INVALID_BATCH: "workBatchLimit", INVALID_DIRECTION: "fieldInvalid", INVALID_REQUEST: "invalidConfig", INVALID_INPUT: "fieldInvalid",
      ENTRY_NOT_FOUND: "entryNotFound", ENTRY_BUSY: "entryBusy", INVALID_NAME: "nameInvalid", INVALID_RETENTION: "retentionInvalid",
      ENTRY_TRASHED: "entryTrashed", ENTRY_NOT_TRASHED: "entryNotTrashed", PARTIAL_DELETE: "partialDelete",
      MANAGED_SOURCE: "managedSourceTrash", DELETE_FAILED: "deleteFailed", OWNER_CONFLICT: "ownerConflict",
      OWNERSHIP_UNCONFIRMED: "ownershipUnconfirmed", ACTIVE_OWNER_REQUIRED: "activeOwnerRequired",
      PAUSE_REQUEST_ALREADY_COMPLETED: "pauseRequestCompleted",
    };
    const key = map[error?.code] || (error?.messageKey && window.CENTER_MESSAGES.en[error.messageKey] ? error.messageKey : null);
    return key ? message(key, error.params) : text(error?.message) || message("unknownError");
  }

  function languageLabel(value) { return message(value === "zh-CN" ? "language_zh" : value === "en" ? "language_en" : "notRecorded"); }
  function formatTime(value) { return fullTime(value); }
  function fullTime(value) { return window.DashboardDate.format(value, state.language) || message('unknownTime'); }
  function fieldLabel(node, key) { node.dataset.label = message(key); }

  function requestState(request) { return text(request?.state).toLowerCase() || "unknown"; }
  function requestIsFresh(request, currentTime = Date.now()) {
    if (state.stale) return false;
    const liveAge = currentTime - Date.parse(request?.liveConfirmedAt);
    return Number.isFinite(liveAge) && liveAge >= 0 && liveAge <= 15000;
  }
  function executionBlockReason(request, currentTime = Date.now()) {
    if (!requestIsFresh(request, currentTime) || requestState(request) !== "running" || text(request?.executionBlockedReason).toLowerCase() !== "unresolved_p1") return "";
    const blockedAt = Date.parse(request.executionBlockedAt);
    if (!Number.isFinite(blockedAt) || blockedAt > currentTime) return "";
    return "unresolved_p1";
  }
  function completedCyclePause(record) {
    return text(record?.state).toLowerCase() === "ended" && record?.terminalReason === "pause_after_cycle";
  }
  function requestDisplayState(request, currentTime = Date.now()) {
    if (completedCyclePause(request)) return "paused";
    const value = requestState(request);
    if (!["starting", "running", "stopping"].includes(value)) return value;
    if (!requestIsFresh(request, currentTime)) return "unknown";
    const blockedReason = text(request?.executionBlockedReason).toLowerCase();
    if (blockedReason) return executionBlockReason(request, currentTime) ? "blocked" : "unknown";
    return value;
  }
  function execution(entry) { return typeof entry?.executionSummary === "object" && entry.executionSummary ? entry.executionSummary : { state: text(entry?.executionSummary) }; }
  function entryState(entry, currentTime = Date.now()) {
    if (entry?.archived) return "archived";
    const summary = execution(entry); const value = text(summary.state).toLowerCase();
    if (completedCyclePause(summary)) return "paused";
    if (value === "read_only") return readonlyObservationState(entry, currentTime) || "unknown";
    if (["blocked", "running", "starting", "stopping"].includes(value)) {
      const request = (state.summary?.currentRequests || [state.summary?.currentRequest]).find((item) => item?.entryId === entry.entryId);
      if (!summary.requestId || summary.requestId !== request?.requestId || entry?.entryId !== request?.entryId) return "unknown";
      const projected = requestDisplayState(request, currentTime);
      if (value === "blocked") return projected === "blocked" && summary.reason === "unresolved_p1" ? "blocked" : "unknown";
      return projected === value ? value : "unknown";
    }
    if (["queued", "attention", "failed", "ended", "canceled", "preparing", "paused", "read_only", "unknown"].includes(value)) return value;
    const availability = entry?.availability?.state || entry?.availability;
    if (["unknown", "unavailable", "conflict"].includes(availability)) return "unknown";
    if (availability === "read_only" || (value === "idle" && entry?.capabilities?.execute === false)) return readonlyObservationState(entry, currentTime) || "unknown";
    return "idle";
  }

  function readonlyObservationState(entry, currentTime = Date.now()) {
    const observation = entry?.readonlyObservation;
    if (state.stale || observation?.readOnly !== true || observation.scoped !== true) return "";
    const age = currentTime - Date.parse(observation.liveConfirmedAt);
    if (["running", "paused", "idle"].includes(observation.state) && Number.isFinite(age) && age >= 0 && age <= 15000) return observation.state;
    const observedAge = currentTime - Date.parse(observation.observedAt);
    return observation.state === "ended" && observation.processState === "stopped" && Number.isFinite(observedAge) && observedAge >= 0 && observedAge <= 15000 ? "ended" : "";
  }

  function statusLabel(value) {
    const key = `state_${value}`;
    return window.CENTER_MESSAGES[state.language][key] || message("state_unknown");
  }
  function filterLabel(value) { const key = `filter${value[0].toUpperCase()}${value.slice(1)}`; return window.CENTER_MESSAGES[state.language][key] || statusLabel(value); }
  function roundLabel(value) { const key = `round_${value}`; return window.CENTER_MESSAGES[state.language][key] || statusLabel(value); }
  function latestWorkSource(entry) {
    const work = entry.latestWork;
    if (!work || typeof work !== "object" || (work.scope === "product" && work.isLatestCycle !== false)) return "";
    const scope = message(work.scope === "exploration" ? "workSourceExploration" : work.scope === "legacy" ? "workSourceLegacy" : "workSourceEarlier");
    return knownNumber(work.cycleNumber) ? message("workSourceCycle", { scope, cycle: String(work.cycleNumber).padStart(2, "0") }) : scope;
  }
  function phaseLabel(value) { const key = `phase_${value}`; return window.CENTER_MESSAGES[state.language][key] || value; }

  function capability(entry, name) {
    const raw = entry?.capabilities?.[name];
    const enabled = raw === true || raw?.enabled === true;
    const availability = typeof entry?.availability === "object" ? entry.availability : {};
    const reason = text(raw?.reason || raw?.reasonCode || entry?.capabilityReasons?.[name] || (["preview", "capture"].includes(name) ? entry?.capabilityReasons?.media : "") || availability?.reasons?.[name] || availability?.reason);
    return { enabled, reason };
  }

  function capabilityReason(reason, fallback = "capabilityUnavailable") {
    if (!reason) return message(fallback);
    const known = { unmanaged_source: "unmanagedSource", read_only_source: "readOnlySource", execution_domain_unconfigured: "executionUnavailable", runtime_incompatible: "runtimeIncompatible", slot_busy: "slotBusy", open_request_exists: "openRequestExists", source_unavailable: "sourceUnavailableReason", entry_archived: "archiveBlocked", product_registration_invalid: "productRegistrationInvalid", context_unavailable: "contextUnavailable", governance_pause: "governancePaused", budget_pause: "budgetPaused", stop_unconfirmed: "stopUnconfirmed", unresolved_p1: "unresolvedP1", framework_unverified: "frameworkUnverified", preparation_failed: "preparationFailed" };
    if (window.CENTER_MESSAGES[state.language][reason]) return message(reason);
    const key = known[reason] || known[String(reason).toLowerCase()];
    return key ? message(key) : errorText({ code: reason });
  }

  function requestReason(reason) {
    const value = text(reason);
    if (value === "user_stop") return message("requestedStop");
    if (value === "user_cancel") return message("requestedCancel");
    if (value === "pause_after_cycle") return message("completedCyclePause");
    return /^(?:PRODUCT_REGISTRATION_INVALID|CONTEXT_UNAVAILABLE|GOVERNANCE_PAUSE|BUDGET_PAUSE|STOP_UNCONFIRMED|UNRESOLVED_P1|FRAMEWORK_UNVERIFIED|PREPARATION_FAILED)$/i.test(value) ? capabilityReason(value) : value || message("unknownError");
  }
  function queueWaitReason() {
    if (state.summary?.dispatchEnabled === false) return message("dispatchOffHint");
    const capacity = state.summary?.maxConcurrentProjects, occupied = state.summary?.occupiedCount;
    return knownNumber(capacity) && knownNumber(occupied) && occupied >= capacity ? message("queueCapacityWait") : message("queueOrderHint");
  }

  async function allEntries(snapshot) {
    const items = []; let cursor = null; let total = null; const seen = new Set();
    do {
      const suffix = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
      const page = await api(`/entries?filter=all&sort=activity&limit=100${suffix}`, {}, 30000, snapshot);
      if (!page || !Array.isArray(page.items)) throw new APIError({ code: "INVALID_RESPONSE" }, 200);
      items.push(...page.items); total = page.total; cursor = page.nextCursor || null;
      if (cursor && seen.has(cursor)) throw new APIError({ code: "INVALID_RESPONSE" }, 200);
      if (cursor) seen.add(cursor);
    } while (cursor);
    if (knownNumber(total) && items.length !== total) throw new APIError({ code: "INVALID_RESPONSE" }, 200);
    return { items, total: total ?? items.length };
  }

  function inProjectList(entry) {
    return entry.kind !== "reference";
  }

  function normalizeCounts() {
    const counts = { all: state.entries.filter((entry) => !entry.archived && inProjectList(entry)).length, running: 0, queued: 0, attention: 0, archived: 0, trash: state.trash?.items?.length || 0 };
    for (const entry of state.entries) {
      const value = entryState(entry);
      if (value === "archived") counts.archived += 1;
      if (inProjectList(entry) && ["running", "starting", "stopping"].includes(value)) counts.running += 1;
      if (inProjectList(entry) && value === "queued") counts.queued += 1;
      if (inProjectList(entry) && ["blocked", "attention", "failed", "unknown"].includes(value)) counts.attention += 1;
    }
    counts.attention += state.operations.filter(item => !item.archived && ["failed", "attention"].includes(item.state)).length;
    return counts;
  }

  function filteredEntries() {
    const query = state.query.toLocaleLowerCase(state.language);
    return (state.filter === "trash" ? state.trash?.items || [] : state.entries).filter((entry) => {
      const value = entryState(entry);
      const filterMatch = state.filter === "all" ? !entry.archived && inProjectList(entry)
        : state.filter === "running" ? inProjectList(entry) && ["running", "starting", "stopping"].includes(value)
        : state.filter === "queued" ? inProjectList(entry) && value === "queued"
        : state.filter === "attention" ? inProjectList(entry) && ["blocked", "attention", "failed", "unknown"].includes(value)
        : state.filter === "archived" ? entry.archived === true
        : state.filter === "trash" ? entry.trashed === true
        : state.filter === "exploration" ? entry.kind === "exploration" && !entry.archived
        : state.filter === "reference" ? entry.kind === "reference" && !entry.archived
        : state.filter === "read_only" ? inProjectList(entry) && !entry.archived && execution(entry).state === "read_only"
        : CATALOG_FILTERS.includes(state.filter) && inProjectList(entry) && value === state.filter;
      if (state.filter === "all" && entry.kind === "reference") return false;
      if (!filterMatch) return false;
      if (state.roundFilter !== "all" && latestRoundState(entry) !== state.roundFilter) return false;
      if (!query) return true;
      return [entry.displayName, entry.description, entry.alias, entry.direction, entry.directionSummary, entry.shortId, entry.createdAt, entry.entryId, entry.productId, entry.explorationId].some((value) => text(value).toLocaleLowerCase(state.language).includes(query));
    });
  }

  function emptyListState(entries = filteredEntries()) {
    if (entries.length) return null;
    if (state.filter === "trash") {
      const trashPart = state.readParts.get("trash");
      if (trashPart?.failed) return { messageKey: "loadFailed" };
      if (!trashPart && (state.loading || state.readParts.size > 0)) return { messageKey: "loading" };
    }
    if (state.stale && !state.entries.length) return { messageKey: "loadFailed" };
    if (state.query || state.filter !== "all" || state.roundFilter !== "all") return { messageKey: "noMatches", actionKey: "clearFilters", target: "all" };
    const hasProduct = state.entries.some((entry) => !entry.archived && ["product", "legacy"].includes(entry.kind));
    if (!hasProduct) return { messageKey: "noFormedProducts", actionKey: "viewExplorations", target: "exploration" };
    return { messageKey: "noProducts" };
  }

  function safeAssetURL(value) {
    if (typeof value !== "string" || !value.startsWith(`${API}/`)) return null;
    try { const url = new URL(value, location.origin); return url.origin === location.origin && url.pathname.startsWith(`${API}/`) ? `${url.pathname}${url.search}` : null; }
    catch (_) { return null; }
  }

  function fallbackIcon(kind) {
    const box = element("span", "product-icon");
    box.append(window.DashboardIcons.icon(kind === "exploration" ? "search" : kind === "legacy" ? "file-text" : "panels-top-left")); return box;
  }

  function entryIcon(entry) {
    const href = safeAssetURL(entry.iconUrl);
    if (!href) return fallbackIcon(entry.kind);
    const box = element("span", "product-icon");
    const image = element("img"); image.src = href; image.alt = ""; image.width = image.height = 42;
    image.addEventListener("error", () => box.replaceChildren(fallbackIcon(entry.kind).firstChild), { once: true });
    box.append(image); return box;
  }

  function entryThumbnail(entry) {
    const box = element("span", "product-thumbnail");
    const href = safeAssetURL(entry.thumbnailUrl);
    const missing = () => { box.classList.add("thumbnail-missing"); box.replaceChildren(entryIcon(entry)); box.title = message("productLogo", { name: entry.displayName || message("fieldMissing") }); box.setAttribute("aria-label", box.title); };
    if (!href) { missing(); return box; }
    const image = element("img"); image.src = href; image.alt = message("productPreview", { name: entry.displayName });
    image.loading = "lazy"; image.decoding = "async";
    box.title = message(entry.thumbnailStale ? "previewPrevious" : "productPreview", { name: entry.displayName });
    image.addEventListener("error", missing, { once: true });
    box.append(image); return box;
  }

  function statusSymbol(value) {
    const normalized = ["pending", "not_started"].includes(value) ? "queued"
      : ["interrupted", "completed_with_timeout"].includes(value) ? "paused" : value;
    const visual = window.DashboardStatus.visual(normalized);
    const node = element("span", `status-symbol ${visual === "pending" ? "queued" : visual}`);
    node.setAttribute("aria-hidden", "true");
    node.append(window.DashboardIcons.status(visual));
    return node;
  }

  function detailURL(entry) { return `/products/${encodeURIComponent(entry.entryId)}`; }
  function sortedEntries(entries = filteredEntries()) {
    const statusOrder = ["running", "starting", "stopping", "queued", "blocked", "attention", "failed", "paused", "idle", "ended", "canceled", "preparing", "read_only", "archived", "unknown"];
    const value = entry => state.sort === "name" ? text(entry.displayName) : state.sort === "work" ? text(entry.latestTitle)
      : state.sort === "status" ? statusOrder.indexOf(entryState(entry))
      : state.sort === "round" ? knownNumber(entry.cycleNumber) ? entry.cycleNumber : null
      : Number.isFinite(Date.parse(entry.lastActivityAt)) ? Date.parse(entry.lastActivityAt) : null;
    return [...entries].sort((left, right) => {
      const a = value(left), b = value(right);
      if (a === null || a === "") return b === null || b === "" ? 0 : 1;
      if (b === null || b === "") return -1;
      const comparison = typeof a === "string" ? a.localeCompare(b, state.language) : a - b;
      return comparison * (state.sortDirection === "desc" ? -1 : 1);
    });
  }
  function columnHeader(label, field, groupKey) {
    const cell = element("th", "column-heading"); cell.setAttribute("role", "columnheader");
    cell.setAttribute("aria-sort", state.sort === field ? state.sortDirection === "asc" ? "ascending" : "descending" : "none");
    cell.dataset.column = field;
    if (field === "preview") {
      cell.removeAttribute("aria-sort");
      const select = focusKey(element("select", "column-select preview-select"), `column:${groupKey}:preview`);
      select.setAttribute("aria-label", message("exampleDisplay"));
      for (const mode of ["logo", "screenshot", "none"]) select.append(new Option(message(`example_${mode}`), mode));
      select.value = state.previewMode;
      select.addEventListener("change", () => { state.previewMode = select.value; saveView(); renderPage(); restoreFocus(`column:${groupKey}:preview`); });
      select.id = `preview-${groupKey}`;
      cell.append(select);
    } else if (["status", "round"].includes(field)) {
      const select = focusKey(element("select", "column-select"), `column:${groupKey}:${field}`);
      select.setAttribute("aria-label", message("columnControl", { column: message(label) }));
      select.append(new Option(message(label), "filter:all"));
      const sortGroup = element("optgroup"); sortGroup.label = message("sortProducts");
      for (const direction of ["asc", "desc"]) sortGroup.append(new Option(message(field === "round" ? direction === "asc" ? "roundAscending" : "roundDescending" : direction === "asc" ? "statusRunningFirst" : "statusUnknownFirst"), `sort:${direction}`));
      select.append(sortGroup);
      const filterGroup = element("optgroup"); filterGroup.label = message("filterProducts");
      const values = field === "status" ? ["running", "queued", "attention", "paused", "ended", "idle", "unknown", "failed", "blocked", "canceled", "preparing", "starting", "stopping", "archived", "reference", "exploration"] : ["completed", "running", "correcting", "validating", "closing", "recovering", "handoff", "failed", "pending", "not_started", "startup_unconfirmed", "interrupted", "completed_with_timeout", "paused", "unknown", "no_rounds"];
      for (const value of values) filterGroup.append(new Option(field === "status" ? filterLabel(value) : roundLabel(value), `filter:${value}`));
      select.append(filterGroup);
      const current = field === "status" ? state.filter : state.roundFilter;
      select.value = values.includes(current) ? `filter:${current}` : state.sort === field ? `sort:${state.sortDirection}` : "filter:all";
      select.addEventListener("change", () => {
        const [kind, value] = select.value.split(":");
        if (kind === "sort") { state.sort = field; state.sortDirection = value; }
        else if (field === "status") state.filter = value;
        else state.roundFilter = value;
        saveView(); renderPage(); restoreFocus(`column:${groupKey}:${field}`);
      });
      cell.append(select);
    } else {
      const button = focusKey(element("button", "column-sort-button", message(label)), `column:${groupKey}:${field}`); button.type = "button";
      const indicator = element("span", "sort-indicator"); indicator.setAttribute("aria-hidden", "true");
      indicator.append(window.DashboardIcons.icon(state.sort === field ? state.sortDirection === "asc" ? "arrow-up" : "arrow-down" : "arrow-up-down")); button.append(indicator);
      button.setAttribute("aria-label", message("sortColumn", { column: message(label) }));
      button.onclick = () => { state.sortDirection = state.sort === field && state.sortDirection === "asc" ? "desc" : "asc"; state.sort = field; saveView(); renderPage(); restoreFocus(`column:${groupKey}:${field}`); };
      cell.append(button);
    }
    return cell;
  }

  function latestRoundState(entry) {
    if (!knownNumber(entry.cycleNumber) && ["", "unknown"].includes(text(entry.latestCycleStatus))) return "no_rounds";
    const recorded = text(entry.latestCycleStatus) || "unknown";
    if (entry.latestHarnessVersion === 2) {
      if (["running", "correcting", "recovering"].includes(recorded) && entry.latestCycleActiveConfirmed !== true) return "unknown";
      return recorded;
    }
    return readonlyObservationState(entry) === "ended" && ["running", "startup_unconfirmed", "pending"].includes(recorded) ? "interrupted" : recorded;
  }

  function latestRound(entry) {
    const cell = element("td", "latest-round"); cell.setAttribute("role", "cell");
    fieldLabel(cell, "latestRound");
    cell.append(element("span", "round-number", knownNumber(entry.cycleNumber) ? `#${String(entry.cycleNumber).padStart(2, "0")}` : "—"));
    if (!knownNumber(entry.cycleNumber)) {
      cell.append(element("span", "round-label", message("noRounds")));
      return cell;
    }
    const value = latestRoundState(entry);
    const label = roundLabel(value);
    const mark = statusSymbol(value);
    const status = element("span", "round-status");
    status.append(mark, element("span", "round-label", label));
    cell.append(status);
    return cell;
  }

  const rowNodes = new Map();
  function rowSignature(entry) {
    return JSON.stringify([entry, state.language, state.previewMode, state.stale, entryState(entry), capability(entry, 'execute'), window.DashboardDate.day()],
      (key, value) => ['observedAt', 'liveConfirmedAt', 'generatedAt'].includes(key) ? undefined : value);
  }
  function renderRow(entry) {
    const signature = rowSignature(entry), cached = rowNodes.get(entry.entryId);
    if (cached?.signature === signature) return cached.row;
    const row = element("tr", "product-row"); row.setAttribute("role", "row"); row.dataset.entryId = entry.entryId;
    const identity = element("td", "product-identity"); identity.setAttribute("role", "cell");
    const copy = element("div");
    const name = element("h3", "product-name");
    const nameText = text(entry.displayName) || message("fieldMissing"); name.title = nameText;
    if (entry.kind !== "reference") {
      const link = focusKey(element("a", "product-link", nameText), `entry:${entry.entryId}:view`); link.href = detailURL(entry); name.append(link);
    } else name.textContent = nameText;
    const description = element("p", "product-description", text(entry.description) || message("purposeMissing"));
    copy.append(name, description); identity.append(copy);
    const preview = element("td", "product-example"); preview.setAttribute("role", "cell");
    if (state.previewMode !== "none") preview.append(state.previewMode === "logo" ? entryIcon(entry) : entryThumbnail(entry));
    if (entry.kind !== "reference") {
      row.classList.add("product-row-link");
      row.addEventListener("click", event => {
        if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey
          || event.target.closest("a, button, input, select, textarea, [role=menuitem]") || window.getSelection()?.toString()) return;
        saveView(); name.querySelector("a").click();
      });
    }

    const recent = element("td", "recent-work"); recent.setAttribute("role", "cell");
    fieldLabel(recent, "recentWork");
    const title = element("p", `work-title${text(entry.latestTitle) ? "" : " work-missing"}`, text(entry.latestTitle) || message("workMissing")); title.title = title.textContent;
    if (text(entry.reportedPhase)) recent.title = message("phaseRecorded", { phase: phaseLabel(entry.reportedPhase) });
    recent.append(title);


    const value = entryState(entry);
    const status = element("td", "status-cell"); status.setAttribute("role", "cell");
    fieldLabel(status, "runtimeStatus");
    const statusCopy = element("div"); statusCopy.append(element("strong", "", statusLabel(value)));
    if (value === "queued" && knownNumber(execution(entry).queuePosition)) {
      statusCopy.append(element("small", "queue-position", message("queuePosition", { position: execution(entry).queuePosition })));
    }
    status.append(statusSymbol(value), statusCopy);

    const activity = element("time", "activity-time");
    if (entry.lastActivityAt && Number.isFinite(Date.parse(entry.lastActivityAt))) {
      const stamp = window.DashboardDate.parts(entry.lastActivityAt, state.language);
      activity.dateTime = entry.lastActivityAt; activity.title = fullTime(entry.lastActivityAt); activity.setAttribute("aria-label", fullTime(entry.lastActivityAt)); activity.tabIndex = 0;
      activity.append(element("span", "activity-date", stamp.date), element("span", "activity-clock", stamp.time));
    } else activity.textContent = message("unknownTime");

    const actions = element("div", "row-actions");
    const execute = capability(entry, "execute");
    const items = [];
    if (["product", "exploration"].includes(entry.kind) && !entry.archived && !entry.trashed) {
      items.push({ label: message("continue"), disabled: !execute.enabled,
        reason: execute.reason ? message("unavailableReason", { reason: capabilityReason(execute.reason) }) : message("capabilityUnavailable"),
        focusKey: `entry:${entry.entryId}:continue-menu`, action: () => openContinue(entry) });
    }
    if (entry.trashed) {
      const deleting = Boolean(entry.deletionInProgress);
      const deletingReason = deleting ? message("actionPending") : "";
      items.push({ label: message("restoreTrash"), disabled: deleting, reason: deletingReason, focusKey: `entry:${entry.entryId}:restore-trash`, action: () => trashEntryAction(entry, "restore-trash") },
        { label: message("deletePermanently"), danger: true, disabled: deleting, reason: deletingReason, focusKey: `entry:${entry.entryId}:delete`, action: () => trashEntryAction(entry, "delete") });
    } else {
      items.push({ label: message("rename"), focusKey: `entry:${entry.entryId}:rename`, action: () => renameEntry(entry) },
        { label: message("manageSources"), focusKey: `entry:${entry.entryId}:manage`, action: () => openSourceManager(entry) },
        { label: message(entry.archived ? "restore" : "archive"), focusKey: `entry:${entry.entryId}:visibility`, action: () => confirmEntryVisibility(entry) },
        { label: message("moveToTrash"), danger: true, focusKey: `entry:${entry.entryId}:trash`, action: () => trashEntryAction(entry, "trash") });
    }
    if (entry.kind === "reference" && !entry.archived && !entry.trashed) items.push({ label: message("detachReference"), danger: true,
      focusKey: `entry:${entry.entryId}:detach`, action: () => confirmReferenceDetach(entry) });
    actions.append(UI.menu({ id: entry.entryId, label: message("moreActions"), items }));
    const updated = element("td", "updated-cell"); updated.setAttribute("role", "cell");
    fieldLabel(updated, "updatedTime");
    activity.removeAttribute("role"); updated.append(activity, actions);
    row.append(preview, identity, status, latestRound(entry), recent, updated);
    rowNodes.set(entry.entryId, { signature, row });
    return row;
  }

  let entriesSignature = '';
  function renderEntries() {
    const container = $("productRows");
    const entries = sortedEntries();
    const trashStatus = state.readParts.get("trash")?.failed ? "failed" : state.readParts.has("trash") ? "ok" : "pending";
    const signature = JSON.stringify([entries.map(rowSignature), state.language, state.stale, state.summary?.executionAvailable, state.query, state.filter, state.sort, state.sortDirection, state.roundFilter, state.otherExpanded, state.loading, trashStatus]);
    if (signature === entriesSignature) return;
    entriesSignature = signature;
    const positions = UI.positions(container, '.product-row');
    const headerKey = JSON.stringify([state.language, state.sort, state.sortDirection, state.roundFilter, state.previewMode]);
    const headers = container.dataset.headerKey === headerKey ? [...container.querySelectorAll('thead')] : [];
    container.dataset.headerKey = headerKey;
    clear(container);
    const listState = clear($("listState"));
    if (state.loading && !state.entries.length) { if (performance.now() - state.loadStarted >= 300) UI.loading(listState, message("loading")); return; }
    announce(message("searchResultCount", { count: entries.length }));
    UI?.retainMenus(entries.map(entry => entry.entryId));
    // The API returns activity order; recent products are independent of execution state.
    const groups = [["recentProducts", entries.slice(0, 4)], ["otherProducts", entries.slice(4)]];
    for (const [groupIndex, [key, items]] of groups.entries()) {
      if (!items.length && groupIndex !== 0) continue;
      const group = element("section", "product-group");
      const heading = element("h2", "product-group-title", message(key).startsWith("filter") ? message("productList") : message(key));
      heading.append(element("span", "count-badge", formatNumber(items.length)));
      const table = element("table", "product-table"); table.setAttribute("aria-label", heading.textContent);
      const head = element("tr", "product-head"); head.setAttribute("role", "row");
      for (const [label, field] of [["example", "preview"], ["productName", "name"], ["runtimeStatus", "status"], ["latestRound", "round"], ["recentWork", "work"], ["updatedTime", "activity"]]) head.append(columnHeader(label, field, groupIndex === 0 ? "primary" : "remaining"));
      const shown = groupIndex === 1 ? items.slice(0, 4) : items;
      const header = element("thead"), body = element("tbody"); header.append(head); body.append(...shown.map(renderRow)); table.append(headers[groupIndex] || header, body); if (items.length) group.append(heading); group.append(table);
      if (groupIndex === 1 && items.length > 4) {
        const disclosure = element("details", "other-products-disclosure"); disclosure.open = state.otherExpanded;
        const label = () => message(state.otherExpanded ? "collapseProducts" : "expandProducts", { count: items.length });
        const trigger = focusKey(element("summary", "text-button", label()), "other-products:toggle");
        if (!state.otherExpanded) trigger.append(element("span", "count-badge", formatNumber(items.length)));
        const remaining = element("table", "product-table"); remaining.setAttribute("aria-label", heading.textContent);
        const remainingBody = element("tbody"); remainingBody.append(...items.slice(4).map(renderRow)); remaining.append(remainingBody);
        disclosure.append(trigger, remaining);
        disclosure.addEventListener("toggle", () => {
          if (!disclosure.isConnected) return;
          state.otherExpanded = disclosure.open;
          const button = disclosure.querySelector(".disclosure-trigger"); button.textContent = label();
          if (!state.otherExpanded) button.append(element("span", "count-badge", formatNumber(items.length)));
        });
        group.append(disclosure);
      }
      container.append(group);
    }
    const retained = new Set(entries.map(entry => entry.entryId));
    for (const key of rowNodes.keys()) if (!retained.has(key)) rowNodes.delete(key);
    UI.layout(container, '.product-row', positions);
    if (!entries.length) {
      const emptyState = emptyListState(entries);
      listState.append(element("span", "", emptyState.messageKey === "noMatches" ? `${message("noMatchesConditions", { query: state.query || message("anyQuery"), filter: filterLabel(state.filter) })}${state.roundFilter !== "all" ? ` ${message("latestRound")}: ${roundLabel(state.roundFilter)}` : ""}` : message(emptyState.messageKey)));
      if (emptyState.actionKey) {
        const action = element("button", "text-button", message(emptyState.actionKey)); action.type = "button";
        action.addEventListener("click", () => { state.query = ""; $("productSearch").value = ""; state.filter = emptyState.target; state.roundFilter = "all"; saveView(); renderPage(); $("productSearch").focus(); });
        listState.append(action);
      }
      if (!["noMatches", "loadFailed"].includes(emptyState.messageKey)) {
        for (const [key, trigger] of [["newWork", "newWorkButton"], ["importAction", "importButton"]]) {
          const action = element("button", key === "newWork" ? "button primary" : "button secondary", message(key)); action.type = "button"; action.disabled = $(trigger).disabled;
          action.onclick = () => $(trigger).click(); listState.append(action);
        }
      }
    }
  }

  function renderActivity() {
    const counts = normalizeCounts();
    const active = state.summary?.currentRequests || [state.summary?.currentRequest].filter(Boolean);
    const unconfirmed = !state.summary || state.stale || active.some((request) => !requestIsFresh(request)) || state.summary.occupiedCount > active.length;
    const summary = clear($("capacitySummary"));
    if (state.loading || unconfirmed) summary.textContent = message(state.loading ? "loading" : "runtimeUnconfirmed");
    else for (const [key, value] of [["capacityRunning", counts.running], ["capacityWaiting", state.summary?.queuedCount ?? counts.queued], ["capacityLimit", state.summary?.maxConcurrentProjects === null ? message("unlimited") : state.summary?.maxConcurrentProjects ?? "—"]]) {
      const row = element("span", "capacity-line", message(key));
      row.append(element("span", "count-badge", String(value))); summary.append(row);
    }
  }

  function renderCounts() {
    const counts = normalizeCounts();
    for (const key of ["All", "Running", "Queued", "Attention", "Archived", "Trash"]) {
      const value = counts[key.toLowerCase()], existing = $(`count${key}`);
      if (!value) { existing?.remove?.(); continue; }
      const count = existing || element("span", "filter-count count-badge"); count.id = `count${key}`; count.textContent = formatNumber(value);
      if (!existing) $("filters").querySelector(`[data-filter="${key.toLowerCase()}"]`).append(count);
    }
    const current = state.summary?.currentRequest;
    const queueCount = (state.summary?.queuedCount || 0) + (state.summary?.attentionCount || 0) + (state.summary?.preparationCount || 0) + (state.summary?.currentRequests ? state.summary.currentRequests.filter((item) => item.state !== "attention").length : current && current.state !== "attention" ? 1 : 0);
    $("queueNavCount").hidden = !queueCount; clear($("queueNavCount")).append(element("span", "count-badge", formatNumber(queueCount)));
  }

  function applyLanguage() {
    if (!view.active) return;
    UI.selectFilter?.(state.filter);
    document.documentElement.lang = state.language;
    document.title = `Autonomous Company · ${message("products")}`;
    document.querySelectorAll("[data-i18n]").forEach((node) => { if (node.closest("button")?.dataset.idleText || node.closest('button[aria-busy="true"]')) return; node.textContent = message(node.dataset.i18n); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => { node.placeholder = message(node.dataset.i18nPlaceholder); });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => { node.setAttribute("aria-label", message(node.dataset.i18nAria)); });
  }

  function renderPage() {
    if (!view.active) return;
    const focused = rememberFocus();
    const languageChanged = document.documentElement.lang !== state.language;
    applyLanguage();
    if (languageChanged) for (const container of document.querySelectorAll(".template-controls")) {
      const scope = container.closest(".work-group, form");
      if (!scope || scope.dataset.templateSubmitting === "true") continue;
      const selectedId = container.querySelector("select")?.value || "", name = container.querySelector(".template-name")?.value;
      const expanded = container.querySelector(".template-editor")?.open;
      renderTemplateControls(scope, selectedId);
      if (name !== undefined) scope.querySelector(".template-name").value = name;
      scope.querySelector(".template-editor").open = Boolean(expanded);
    }
    $("newWorkButton").disabled = state.stale || state.summary?.executionAvailable === false;
    renderActivity(); renderCounts(); renderEntries(); renderQueue();
    if ($("newWorkDialog").open) updateGroupButtons();
    const executionAvailable = state.summary?.executionAvailable !== false;
    $("newWorkButton").disabled = state.stale || !executionAvailable;
    const trashPart = state.readParts.get("trash");
    if ($("trashSettingsButton")) $("trashSettingsButton").disabled = state.stale || !trashPart || Boolean(trashPart.failed);
    $("newWorkButton").title = !executionAvailable ? message("executionUnavailable") : "";
    $("newWorkUnavailable").hidden = executionAvailable && !state.stale;
    $("newWorkUnavailable").textContent = state.stale ? message("staleActionsDisabled") : !executionAvailable ? message("executionUnavailable") : "";
    $("connectionNotice").hidden = !state.stale;
    if (state.stale) {
      clear($("connectionNotice")).append(UI.alertMessage(message(state.entries.length ? "staleData" : "loadFailed") + (state.lastSuccessAt ? ` ${message("observedStale", { time: fullTime(state.lastSuccessAt) })}` : "")));
      const retry = element("button", "text-button", message("retry")); retry.type = "button"; retry.onclick = refresh; $("connectionNotice").querySelector("[data-slot=alert-description]").append(retry);
    }
    $("observedAt").textContent = state.lastSuccessAt ? message(state.stale ? "observedStale" : "refreshedAt", { time: fullTime(state.lastSuccessAt) }) : "";
    $("observedAt").title = fullTime(state.lastSuccessAt); $("observedAt").setAttribute("aria-label", fullTime(state.lastSuccessAt));
    document.querySelectorAll(".filter-button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.filter === state.filter)));
    window.DashboardIcons.hydrate(view.root);
    state.projectionSignature = runtimeProjectionSignature();
    UI?.mountControls();
    restoreFocus(focused);
  }

  function runtimeProjectionSignature(currentTime = Date.now()) {
    return JSON.stringify({
      stale: state.stale, day: window.DashboardDate.day(),
      current: requestDisplayState(state.summary?.currentRequest, currentTime),
      entries: state.entries.map((entry) => [entry.entryId, entryState(entry, currentTime), readonlyObservationState(entry, currentTime)]),
      requests: state.requests.map((request) => [request.requestId, requestDisplayState(request, currentTime)]),
    });
  }

  function refreshRuntimeProjection(currentTime = Date.now()) {
    if (state.readParts.size) updateReadHealth();
    const signature = runtimeProjectionSignature(currentTime);
    if (signature === state.projectionSignature) return;
    const focused = rememberFocus();
    renderActivity(); renderCounts(); renderEntries(); renderQueue();
    state.projectionSignature = signature;
    UI?.mountControls();
    restoreFocus(focused);
  }

  function queueGroups() {
    const groups = { running: [], queued: [], attention: [], history: [], preparing: [], operationAttention: [], operationHistory: [] };
    for (const request of state.requests) {
      const value = requestState(request);
      if (["running", "starting", "stopping"].includes(value)) groups.running.push(request);
      else if (value === "queued") groups.queued.push(request);
      else if (value === "attention") groups.attention.push(request);
      else if (TERMINAL_STATES.has(value)) groups.history.push(request);
      else if (value === "preparing") groups.attention.push(request);
    }
    for (const operation of state.operations) {
      if (operation.archived || operation.state === "canceled") groups.operationHistory.push(operation);
      else if (operation.state === "preparing") groups.preparing.push(operation);
      else if (["failed", "attention"].includes(operation.state)) groups.operationAttention.push(operation);
      else if (operation.state === "succeeded") groups.operationHistory.push(operation);
    }
    groups.queued.sort((a, b) => (a.queuePosition ?? a.order ?? a.position ?? Infinity) - (b.queuePosition ?? b.order ?? b.position ?? Infinity));
    return groups;
  }

  function requestOwnsDispatch(request) {
    return Boolean(text(request?.dispatchId)) && ["starting", "running", "stopping", "attention"].includes(requestState(request));
  }

  const queueNodes = new Map();
  function queueItem(request, index, group, queued) {
    const signature = JSON.stringify([request, index, group, queued.map(item => item.requestId), requestDisplayState(request), state.language, state.stale, queueWaitReason(), [...state.actionLocks]],
      (key, value) => key === 'observedAt' || key === 'liveConfirmedAt' ? undefined : value);
    const cached = queueNodes.get(request.requestId);
    if (cached?.signature === signature) return cached.node;
    const item = cached?.node || element("article", "queue-item"); item.replaceChildren(); item.dataset.requestId = request.requestId;
    item.append(element("span", "queue-number", group === "queued" ? String(index + 1).padStart(2, "0") : ""));
    const body = element("div"); body.append(element("h4", "", text(request.displayName) || message(`kind_${request.kind}`)));
    const value = requestState(request);
    const displayValue = requestDisplayState(request);
    const activeCycle = ["starting", "running", "stopping"].includes(value) && request.cycleNumber;
    body.append(element("p", "", `${statusLabel(displayValue)}${activeCycle ? ` · ${message("cycleNumber", { number: String(activeCycle).padStart(2, "0") })}` : ""}`));
    const config = request.config || {};
    if (config.model || config.effort) body.append(element("p", "", message("plannedConfig", { model: config.model || message("notRecorded"), effort: config.effort || message("notRecorded") })));
    if (config.productLanguage) body.append(element("p", "", message("languageConfig", { language: languageLabel(config.productLanguage) })));
    const reason = executionBlockReason(request) || request.reasonDetail || request.attentionReason || request.terminalReason;
    if (reason) body.append(element("p", "", message("attentionReason", { reason: requestReason(reason) })));
    if (group === "queued") body.append(element("p", "", queueWaitReason()));
    if (displayValue === "unknown") body.append(element("p", "", `${message("evidenceMissing")} ${message("lastEvidence", { time: fullTime(request.liveConfirmedAt) })}`));
    const actions = element("div", "queue-actions");
    if (["running", "starting", "stopping"].includes(value)) {
      const stop = focusKey(element("button", "text-button danger", message("stopItem")), `request:${request.requestId}:stop`); stop.type = "button"; stop.disabled = value === "stopping" || state.stale; stop.addEventListener("click", () => confirmRequestAction(request, "stop")); actions.append(stop);
      if (value === "running") {
        const waiting = request.pauseAfterCycle?.state === "requested";
        const confirmed = requestIsFresh(request);
        const pause = focusKey(element("button", "text-button", message(waiting ? "cancelPauseAfterCycle" : "pauseAfterCycle")), `request:${request.requestId}:pause`);
        pause.type = "button"; pause.disabled = state.stale || !confirmed || Boolean(request.stopRequested);
        pause.addEventListener("click", () => runRequestAction(request, waiting ? "cancel-pause-after-cycle" : "pause-after-cycle"));
        actions.append(pause);
        if (waiting) body.append(element("p", "", message("pauseAfterCycleWaiting")));
      }
    } else if (group === "queued") {
      const up = focusKey(element("button", "text-button", message("moveUp")), `request:${request.requestId}:up`); up.type = "button"; up.disabled = index === 0 || state.stale; up.addEventListener("click", () => moveRequest(index, -1, queued));
      const down = focusKey(element("button", "text-button", message("moveDown")), `request:${request.requestId}:down`); down.type = "button"; down.disabled = index === queued.length - 1 || state.stale; down.addEventListener("click", () => moveRequest(index, 1, queued));
      const cancel = focusKey(element("button", "text-button danger", message("cancelItem")), `request:${request.requestId}:cancel`); cancel.type = "button"; cancel.disabled = state.stale; cancel.addEventListener("click", () => confirmRequestAction(request, "cancel"));
      actions.append(up, down, cancel);
      if (state.stale) actions.append(element("small", "disabled-reason", message("staleActionsDisabled")));
      else if (index === 0 || index === queued.length - 1) actions.append(element("small", "disabled-reason", [index === 0 ? message("firstQueueItem") : "", index === queued.length - 1 ? message("lastQueueItem") : ""].filter(Boolean).join(" ")));
    } else if (group === "attention") {
      if (requestOwnsDispatch(request)) {
        const stop = focusKey(element("button", "text-button danger", message("stopItem")), `request:${request.requestId}:stop`); stop.type = "button"; stop.disabled = state.stale; stop.addEventListener("click", () => confirmRequestAction(request, "stop")); actions.append(stop);
      }
      const reconcile = focusKey(element("button", "text-button", message("reconcile")), `request:${request.requestId}:reconcile`); reconcile.type = "button"; reconcile.disabled = state.stale || state.actionLocks.has(`request:${request.requestId}`); reconcile.addEventListener("click", async () => {
        const focusedOnStart = document.activeElement === reconcile;
        reconcile.disabled = true;
        try { await runRequestAction(request, "reconcile", true); }
        catch (error) { showStatus("requestFailed", { detail: errorText(error) }, true); }
        finally {
          const focused = rememberFocus();
          const restoreOrigin = focusedOnStart && (document.activeElement === document.body || document.activeElement === reconcile || document.activeElement?.dataset.dialogId === "queueDrawer")
            && state.drawerOpen && !document.querySelector("dialog[open]");
          renderQueue();
          if (focused) restoreFocus(focused);
          else if (restoreOrigin) restoreFocus(reconcile.dataset.focusKey);
        }
      }); actions.append(reconcile);
    }
    item.append(body, actions); queueNodes.set(request.requestId, { signature, node: item }); return item;
  }

  function operationItem(operation) {
    const item = element("article", "queue-item");
    item.append(element("span", "queue-number", ""));
    const body = element("div");
    body.append(element("h4", "", message("preparationItem")));
    body.append(element("p", "", message(operation.state === "canceled" ? "state_canceled" : operation.state === "succeeded" ? "preparationSucceeded" : operation.state === "preparing" ? "state_preparing" : operation.state === "attention" ? "state_attention" : "state_failed")));
    if (operation.reason) body.append(element("p", "", message("attentionReason", { reason: requestReason(operation.reason) })));
    if (operation.createdAt) body.append(element("p", "", message("createdAt", { time: formatTime(operation.createdAt) })));
    const actions = element("div", "queue-actions");
    if (!operation.archived && ["failed", "attention"].includes(operation.state)) {
      for (const [action, key, enabled] of [["retry", "retryPreparation", operation.canRetry], ["restore-draft", "restorePreparationDraft", true], ["cancel", "cancelPreparation", operation.canCancel], ["archive", "archivePreparation", true]]) {
        const button = focusKey(element("button", "text-button", message(key)), `operation:${operation.operationId}:${action}`);
        button.type = "button"; button.disabled = state.stale || enabled === false || state.actionLocks.has(`operation:${operation.operationId}`);
        button.onclick = () => preparationAction(operation, action); actions.append(button);
      }
    }
    item.append(body, actions); return item;
  }

  function operationSection(titleKey, items) {
    const section = element("section", "queue-section");
    const heading = element("h3", "count-heading", message(titleKey));
    heading.append(element("span", "count-badge", formatNumber(items.length))); section.append(heading);
    items.forEach((operation) => section.append(operationItem(operation)));
    return section;
  }

  function queueSection(titleKey, items, group, queued) {
    const section = element("section", "queue-section");
    const heading = element("h3", "count-heading", message(titleKey));
    heading.append(element("span", "count-badge", formatNumber(items.length))); section.append(heading);
    items.forEach((request, index) => section.append(queueItem(request, index, group, queued)));
    return section;
  }

  const queuePreviews = new Map();
  function renderQueueSidebar(groups) {
    const content = $("queueSidebarContent"), nodes = [];
    const positions = UI.positions(content, '.queue-preview');
    const requests = groups.queued;
    clear($("queueSidebarCount")).append(element("span", "count-badge", formatNumber(requests.length)));
    for (const request of requests) {
      const index = groups.queued.indexOf(request);
      const signature = JSON.stringify([request.requestId, request.displayName, request.kind, request.createdAt, index, requestDisplayState(request), queueWaitReason(), state.language, state.entries.find(entry => entry.entryId === request.entryId)?.description]);
      const cached = queuePreviews.get(request.requestId);
      if (cached?.signature === signature) { nodes.push(cached.node); continue; }
      const item = cached?.node || element("article", "queue-preview"); item.replaceChildren(); item.dataset.requestId = request.requestId;
      item.append(element("span", "queue-preview-number", requestState(request) === "queued" ? String(groups.queued.indexOf(request) + 1) : "!"));
      const body = element("div", "queue-preview-body");
      const name = element(request.entryId ? "a" : "strong", "queue-preview-name", text(request.displayName) || message(`kind_${request.kind}`));
      if (request.entryId) { name.href = `/products/${encodeURIComponent(request.entryId)}`; focusKey(name, `queue-preview:${request.requestId}:view`); }
      const entry = state.entries.find((entry) => entry.entryId === request.entryId);
      body.append(name);
      if (entry?.description) body.append(element("p", "", entry.description));
      body.append(element("p", "", `${statusLabel(requestDisplayState(request))}${request.createdAt ? ` · ${formatTime(request.createdAt)}` : ""}`));
      body.append(element("p", "", queueWaitReason()));
      const more = focusKey(element("button", "more-button"), `queue-preview:${request.requestId}`); more.type = "button"; more.append(window.DashboardIcons.icon("ellipsis-vertical"));
      more.setAttribute("aria-label", `${message("queueControls")} · ${name.textContent}`); more.addEventListener("click", openQueue);
      item.append(body, more); nodes.push(item); queuePreviews.set(request.requestId, { signature, node: item });
    }
    UI.reconcile(content, nodes); UI.layout(content, '.queue-preview', positions);
    const retained = new Set(requests.map(request => request.requestId));
    for (const key of queuePreviews.keys()) if (!retained.has(key)) queuePreviews.delete(key);
  }

  let queueSignature = "";
  function renderQueue() {
    const capacity = $("capacityForm");
    if (capacity && !capacity.dataset.dirty) {
      capacity.elements.unlimited.checked = state.summary?.maxConcurrentProjects === null;
      capacity.elements.capacity.value = state.summary?.maxConcurrentProjects ?? 4;
      capacity.elements.capacity.disabled = capacity.elements.unlimited.checked;
    }
    const enabled = state.summary?.dispatchEnabled === true;
    $("dispatchLabel").textContent = message(enabled ? "dispatchOn" : "dispatchOff");
    $("dispatchHint").textContent = message(enabled ? "dispatchOnHint" : "dispatchOffHint");
    $("dispatchButton").textContent = message(enabled ? "pauseQueue" : "resumeQueue");
    $("dispatchButton").disabled = state.stale || state.actionLocks.has("dispatch") || (!enabled && state.summary?.executionAvailable === false);
    $("dispatchButton").title = !enabled && state.summary?.executionAvailable === false ? message("executionUnavailable") : "";
    if ($("dispatchButton").disabled) $("dispatchHint").textContent += ` ${message(state.stale ? "staleActionsDisabled" : "executionUnavailable")}`;
    const groups = queueGroups();
    const signature = JSON.stringify([groups, state.language, state.stale, state.historyVisible, state.entries.map(entry => [entry.entryId, entry.description]), queueWaitReason(), state.requests.map(request => requestDisplayState(request)), [...state.actionLocks]],
      (key, value) => key === 'observedAt' || key === 'liveConfirmedAt' ? undefined : value);
    if (signature === queueSignature) return;
    queueSignature = signature;
    const content = $("queueContent"), positions = UI.positions(content, '.queue-item');
    clear(content);
    renderQueueSidebar(groups);
    if (groups.running.length) content.append(queueSection("runningSection", groups.running, "running", groups.queued));
    if (groups.preparing.length) content.append(operationSection("preparingSection", groups.preparing));
    if (groups.queued.length) content.append(queueSection("queuedSection", groups.queued, "queued", groups.queued));
    if (groups.attention.length) content.append(queueSection("attentionSection", groups.attention, "attention", groups.queued));
    if (groups.operationAttention.length) content.append(operationSection("preparationAttentionSection", groups.operationAttention));
    if (state.historyVisible && groups.history.length) content.append(queueSection("historySection", groups.history, "history", groups.queued));
    if (state.historyVisible && groups.operationHistory.length) content.append(operationSection("preparationHistorySection", groups.operationHistory));
    if (!groups.running.length && !groups.preparing.length && !groups.queued.length && !groups.attention.length && !groups.operationAttention.length && !(state.historyVisible && (groups.history.length || groups.operationHistory.length))) content.append(element("p", "list-state", message("queueEmpty")));
    $("queueHistoryButton").textContent = message(state.historyVisible ? "hideHistory" : "showHistory");
    UI.layout(content, '.queue-item', positions);
    const retained = new Set(state.requests.map(request => request.requestId));
    for (const key of queueNodes.keys()) if (!retained.has(key)) queueNodes.delete(key);
    const ownedAttention = groups.attention.some(requestOwnsDispatch);
    $("stopAllButton").disabled = state.stale || (!groups.running.length && !groups.preparing.length && !groups.queued.length && !ownedAttention);
    $("stopAllReason").textContent = $("stopAllButton").disabled ? message(state.stale ? "staleActionsDisabled" : "noActiveWork") : "";
  }

  function updateReadHealth() {
    const required = ['entries', 'summary', 'requests', 'operations'].map(kind => state.readParts.get(kind));
    state.stale = required.some(part => !part || part.failed || Date.now() - part.receivedAt > 15000);
    if (!state.stale && required.every(part => part.round === state.refreshToken)) {
      const latest = required.reduce((previous, part) => (part.revision ?? -1) > (previous.revision ?? -1) || part.revision === previous.revision && part.observedAt > previous.observedAt ? part : previous);
      state.revision = latest.revision; state.observedAt = latest.observedAt;
      state.apiCenterId = state.centerId; state.apiRevision = Math.max(state.apiRevision ?? 0, state.revision ?? 0);
      state.lastSuccessAt = state.observedAt;
    }
    if (state.revision === null) state.stale = true;
  }
  function installReadPart(kind, data, metadata, generation) {
    if (!view.active || generation !== state.writeGeneration) return;
    if (kind === 'entries') {
      if (state.centerId !== metadata.centerId) {
        state.centerId = metadata.centerId; state.readParts.clear(); state.summary = null; state.trash = { retentionDays: 30, revision: 1, items: [] }; state.requests = []; state.operations = []; state.preferences = null;
        state.revision = null; state.apiRevision = null; state.apiCenterId = metadata.centerId;
      }
    } else if (metadata.centerId !== state.centerId) {
      state.stagedParts.set(kind, { data, metadata, generation }); return;
    }
    const previous = state.readParts.get(kind);
    if (previous && metadata.revision < previous.revision) return;
    state.readParts.set(kind, { ...metadata, receivedAt: Date.now(), failed: false });
    if (kind === 'entries') { state.entries = data.items; state.loading = false; }
    else if (kind === 'trash') state.trash = data;
    else if (kind === 'summary') state.summary = data;
    else if (kind === 'requests' || kind === 'operations') state[kind] = data.items;
    else state.preferences = data;
    const language = state.summary?.language || state.preferences?.language;
    if (['en', 'zh-CN'].includes(language)) state.language = language;
    updateReadHealth(); renderPage();
    if (kind === 'entries') {
      for (const [part, staged] of state.stagedParts) {
        state.stagedParts.delete(part);
        if (staged.metadata.centerId === state.centerId) installReadPart(part, staged.data, staged.metadata, staged.generation);
      }
      if (state.restoreScroll !== null) { window.scrollTo(0, state.restoreScroll); state.restoreScroll = null; }
    }
  }
  function readPart(kind, path) {
    const generation = state.writeGeneration;
    const pending = state.pendingParts.get(kind);
    if (pending?.generation === generation) return pending.promise;
    const metadata = { centerId: state.centerId, revision: null, observedAt: null, round: state.refreshToken };
    const promise = (async () => { try {
      const data = kind === 'entries' ? await allEntries(metadata) : await api(path, {}, 15000, metadata);
      if (kind !== 'summary' && kind !== 'preferences' && !Array.isArray(data?.items) || !data || !metadata.centerId) throw new APIError({ code: 'INVALID_RESPONSE' }, 200);
      installReadPart(kind, data, metadata, generation);
    } catch (error) {
      if (error.name !== 'AbortError' && view.active && generation === state.writeGeneration) {
        state.readParts.set(kind, { ...state.readParts.get(kind), failed: true });
        if (kind === 'entries') state.loading = false;
        updateReadHealth(); renderPage();
      }
    } finally { if (state.pendingParts.get(kind)?.promise === promise) state.pendingParts.delete(kind); } })();
    state.pendingParts.set(kind, { promise, generation }); return promise;
  }
  async function refresh() {
    if (!view.active) return;
    if (state.refreshing) {
      const pending = state.refreshing, generation = state.refreshGeneration;
      await pending;
      if (generation < state.writeGeneration) return refresh();
      return;
    }
    const generation = state.writeGeneration; state.refreshGeneration = generation;
    ++state.refreshToken;
    const promise = (async () => {
      try {
        const entries = readPart('entries', '/entries');
        readPart('summary', '/summary'); readPart('requests', '/requests?limit=100');
        readPart('operations', '/operations'); readPart('preferences', '/preferences');
        readPart('trash', '/trash');
        await entries;
      } finally {
        state.refreshing = null; clearTimeout(state.timer); if (view.active && state.autoRefresh) state.timer = setTimeout(refresh, state.stale ? 15000 : 5000);
      }
    })();
    state.refreshing = promise; return promise;
  }

  function showStatus(key, values = {}, isError = false) {
    if (!isError) UI.notify(message(key, values));
    if (isError) { $("actionError").hidden = false; $("actionError").replaceChildren(UI.alertMessage(message(key, values))); }
    else { $("actionError").hidden = true; $("actionError").textContent = ""; }

  }

  function setFormStatus(form, value, isError = false) {
    const node = form.querySelector(".form-status"); node.textContent = value; node.classList.toggle("error", isError);
  }
  function beginSubmission(form, key = "actionPending", button = form.querySelector('[type="submit"]')) {
    if (form.dataset.submitting === "true") return false;
    form.dataset.submitting = "true"; form.setAttribute("aria-busy", "true");
    if (button) { button.dataset.idleText = button.textContent; button.disabled = true; button.textContent = message(key); }
    setFormStatus(form, `${message(key)} ${message("pendingCloseHint")}`); return true;
  }
  function reserveSubmissionWidth(button) {
    if (!button) return;
    const context = document.createElement("canvas").getContext("2d"), style = getComputedStyle(button);
    if (!context) return;
    context.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
    const formId = button.closest("form")?.id;
    const keys = button.id === "centerRefreshButton" ? ["loading"] : button.id === "commitImportButton" ? ["actionPending"]
      : ["newWorkForm", "continueForm"].includes(formId) ? ["submittingQueue", "submittingStart"] : ["settingsForm", "capacityForm"].includes(formId) ? ["saving"] : formId === "importForm" ? ["probing"] : ["actionPending"];
    const labels = [button.textContent, ...keys.map(key => message(key))];
    const width = Math.ceil(Math.max(...labels.map(label => context.measureText(label).width)) + parseFloat(style.paddingLeft) + parseFloat(style.paddingRight) + parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth));
    button.style.minWidth = `min(${width}px, 100%)`;
  }
  function endSubmission(form, button = form.querySelector('[type="submit"]')) {
    delete form.dataset.submitting; form.removeAttribute("aria-busy");
    if (button) { button.disabled = false; button.textContent = button.dataset.idleText || button.textContent; delete button.dataset.idleText; }
  }
  function clearFieldError(field) {
    if (!field.dataset.errorId) return;
    $(field.dataset.errorId)?.remove(); field.removeAttribute("aria-invalid");
    const ids = (field.getAttribute("aria-describedby") || "").split(/\s+/).filter(id => id && id !== field.dataset.errorId);
    if (ids.length) field.setAttribute("aria-describedby", ids.join(" ")); else field.removeAttribute("aria-describedby");
    delete field.dataset.errorId;
  }
  function markFieldError(field, key) {
    clearFieldError(field);
    const id = `${field.closest("form")?.id || "field"}-${field.closest(".work-group")?.id || ""}-${field.name}-error`;
    const validity = field.validity;
    const error = element("small", "field-error", message(key || (validity.valueMissing ? "fieldRequired" : validity.rangeUnderflow || validity.rangeOverflow ? "fieldRange" : "fieldInvalid"), { min: field.min || "1", max: field.max || "∞" }));
    error.id = id; error.setAttribute("role", "alert"); field.after(error); field.dataset.errorId = id;
    field.setAttribute("aria-invalid", "true"); field.setAttribute("aria-describedby", `${field.getAttribute("aria-describedby") || ""} ${id}`.trim());
  }

  function fillDefaults(form, productLanguage) {
    const defaults = state.preferences?.defaults || state.preferences || state.summary?.defaults || {};
    for (const name of ["engine", "model", "effort", "productLanguage"]) {
      const field = form.querySelector(`[name="${name}"]`); if (!field) continue;
      field.value = name === "productLanguage" && productLanguage ? productLanguage : defaults[name] || (name === "effort" ? "high" : name === "productLanguage" ? "zh-CN" : "");
    }
  }

  function openDialog(dialog) {
    if (!dialog.open && !dialog.closest("[data-motion-exit]")) {
      state.dialogToken += 1;
      const form = dialog.querySelector("form"); if (form) endSubmission(form);
      if (dialog.id === "newWorkDialog") { state.workSubmitting = false; updateGroupButtons(); }
    }
    UI?.mountControls();
    dialog.querySelectorAll("[data-error-id]").forEach(clearFieldError); dialog.showModal();
    dialog.querySelectorAll('[type="submit"], #commitImportButton, #centerRefreshButton').forEach(reserveSubmissionWidth);
    if (!UI) dialog.querySelector("input:not([type=radio]), textarea, select")?.focus();
  }
  function closeDialog(dialog) { if (dialog.id === "importDialog") resetImportProbe(); if (dialog.open) dialog.close(); }

  function openContinue(entry) {
    state.menuEntryId = null; state.activeEntry = entry;
    const form = $("continueForm"); form.reset(); fillDefaults(form, entry.productLanguage || entry.language); renderTemplateControls(form);
    $("continueProduct").textContent = `${text(entry.displayName) || message("fieldMissing")} · ${text(entry.description) || message("purposeMissing")}`;
    const cap = capability(entry, "execute");
    $("continueCapability").hidden = cap.enabled && !state.stale; $("continueCapability").textContent = state.stale ? message("staleActionsDisabled") : cap.reason ? message("unavailableReason", { reason: capabilityReason(cap.reason) }) : message("capabilityUnavailable");
    form.querySelector('[type="submit"]').disabled = !cap.enabled || state.stale;
    setFormStatus(form, ""); openDialog($("continueDialog"));
  }

  function formConfig(form) {
    return Object.fromEntries(["engine", "model", "effort", "productLanguage"].map((name) => [name, text(form.querySelector(`[name="${name}"]`)?.value)]));
  }

  function setupGroup(group) {
    group.querySelectorAll(".field-error").forEach(node => node.remove());
    group.querySelectorAll("[data-error-id]").forEach(field => { field.removeAttribute("aria-invalid"); field.removeAttribute("aria-describedby"); delete field.dataset.errorId; });

    group.id = `work-group-${++state.nextWorkGroupId}`;
    group.setAttribute("aria-labelledby", `${group.id}-tab`);
    state.activeWorkGroupId = group.id;
    fillDefaults(group);
    group.querySelector('[name="count"]').value = "1";
    group.querySelector('[name="direction"]').value = "";
    renderTemplateControls(group);
    group.querySelector(".remove-group").onclick = () => {
      if ($("workGroups").children.length <= 1) return;
      const next = group.nextElementSibling || group.previousElementSibling;
      group.remove(); state.activeWorkGroupId = next.id;
      updateGroupButtons();
      $(`${next.id}-tab`).focus();
    };
    group.oninput = updateGroupButtons;
    group.onchange = updateGroupButtons;
    group.querySelectorAll("[data-count-step]").forEach((button) => {
      button.onclick = () => {
        const count = group.querySelector('[name="count"]');
        count.value = Math.min(100, Math.max(1, (Number(count.value) || 1) + Number(button.dataset.countStep)));
        updateGroupButtons();
      };
    });
    group.querySelector(".save-work-template").onclick = () => {
      group.querySelector(".template-editor").open = true;
      group.querySelector(".template-name").focus();
    };
    UI?.mountControls(group);
    updateGroupButtons();
  }

  function selectWorkGroup(group) {
    const changed = state.activeWorkGroupId !== group.id;
    state.activeWorkGroupId = group.id;
    updateGroupButtons();
    if (changed) UI.reveal(group);
  }

  function updateGroupButtons() {
    const groups = [...$("workGroups").children], tabs = $("workGroupTabs");
    let total = 0;
    const options = [];
    groups.forEach((group, index) => {
      const count = Math.max(0, Number(group.querySelector('[name="count"]').value) || 0);
      total += count;
      const templateId = group.querySelector(".template-select")?.value;
      const template = state.preferences?.templates?.find(item => item.templateId === templateId);
      const title = template?.name || message("workGroupNumber", { number: index + 1 });
      options.push({ id: group.id, title, detail: message("workGroupDetail", { effort: group.querySelector('[name="effort"]').value, count }) });
      const selected = group.id === state.activeWorkGroupId;
      group.hidden = !selected;
      group.querySelector(".remove-group").hidden = groups.length === 1;
      group.querySelectorAll("[data-count-step]").forEach(control => { control.disabled = Number(control.dataset.countStep) < 0 ? count <= 1 : count >= 100; });
    });
    UI.groupTabs(tabs, options, state.activeWorkGroupId, id => selectWorkGroup($(id)));
    $("workBatchSummary").textContent = message("workBatchSummary", { count: total, groups: groups.length });
    const form = $("newWorkForm"), submit = form.querySelector('[type="submit"]');
    if (!state.workSubmitting) { submit.textContent = message("workCreateProjects", { count: total }); reserveSubmissionWidth(submit); }
    submit.disabled = state.stale || state.workSubmitting || total > 100;
    const capacity = state.summary?.maxConcurrentProjects;
    $("workExecutionHint").textContent = state.stale ? message("staleActionsDisabled") : total > 100 ? message("workBatchLimit")
      : form.elements.executionMode.value === "enqueue" ? message("workEnqueueHint")
      : capacity === null ? message("workUnlimitedHint") : message("workCapacityHint", { count: capacity ?? 4 });
  }

  function renderTemplateControls(scope, selectedId = state.preferences?.defaultTemplateId || "") {
    const container = scope.querySelector(".template-controls");
    if (!container) return;
    const workGroup = scope.classList.contains("work-group");
    let loadedRevision = state.preferences?.revision;
    let contextToken = state.dialogToken;
    const isCurrent = () => scope.isConnected && contextToken === state.dialogToken;
    clear(container);
    const label = element("label"); label.append(element("span", "", message("configurationTemplate")));
    const select = element("select"); select.classList.add("template-select");
    select.append(new Option(message("automaticConfiguration"), ""));
    for (const template of state.preferences?.templates || []) {
      select.append(new Option(template.name + ((state.preferences.templates || []).filter(item => item.name === template.name).length > 1 ? ` · ${template.config?.model || template.config?.engine || template.templateId.slice(-8)}` : "") + (template.templateId === state.preferences.defaultTemplateId ? ` · ${message("defaultTemplate")}` : ""), template.templateId));
    }
    select.value = selectedId;
    label.append(select); container.append(label);
    const editor = element("details", "template-editor");
    editor.append(element("summary", workGroup ? "template-manage-toggle" : "", message(workGroup ? "workManageTemplates" : "manageTemplates")));
    if (workGroup) editor.id = `${scope.id}-templates`;
    const nameLabel = element("label"); nameLabel.append(element("span", "", message("templateName")));
    const name = element("input"); name.maxLength = 80; name.autocomplete = "off"; name.classList.add("template-name");
    name.name = "templateName";
    nameLabel.append(name); editor.append(nameLabel);
    const controls = element("div", "template-actions");
    const status = element("p", "template-status"); status.setAttribute("role", "status");
    const selected = () => (state.preferences?.templates || []).find((item) => item.templateId === select.value);
    name.value = selected()?.name || "";
    const buttons = [];
    const addAction = (key, action) => {
      const button = element("button", "text-button", message(key)); button.type = "button";
      button.addEventListener("click", async () => {
        if (key === "saveTemplate" && !text(name.value)) { markFieldError(name, "fieldRequired"); name.focus(); return; }
        if (scope.dataset.templateSubmitting === "true") return;
        contextToken = state.dialogToken;
        scope.dataset.templateSubmitting = "true";
        buttons.forEach((item) => { item.disabled = true; }); status.textContent = message("actionPending");
        try {
          const mutation = action();
          const result = await write("/templates", { ...mutation, expectedRevision: loadedRevision });
          const preferences = await api("/preferences"); if (!isCurrent()) return; state.preferences = preferences;
          for (const other of document.querySelectorAll(".template-controls")) {
            const otherScope = other.closest(".work-group, form");
            if (otherScope && otherScope !== scope) renderTemplateControls(otherScope, other.querySelector("select")?.value || "");
          }
          renderTemplateControls(scope, result.template?.templateId && mutation.action !== "delete" ? result.template.templateId : "");
          scope.querySelector(".template-editor").open = true;
          scope.querySelector(".template-status").textContent = message("templateSaved");
        } catch (error) {
          if (isCurrent()) { status.textContent = errorText(error); reload.hidden = error.code !== "REVISION_CONFLICT"; }
        }
        finally { delete scope.dataset.templateSubmitting; buttons.forEach((item) => { item.disabled = false; }); updateActions(); }
      });
      controls.append(button); buttons.push(button); return button;
    };
    addAction("saveTemplate", () => ({ action: "save", name: name.value,
      ...(selected()?.name === name.value.trim() ? { templateId: select.value } : {}), config: formConfig(scope) }));
    const makeDefault = addAction("setDefaultTemplate", () => ({ action: "default", templateId: select.value || null }));
    const remove = addAction("deleteTemplate", () => ({ action: "delete", templateId: select.value }));
    const disabledHint = element("small", "disabled-reason"); controls.append(disabledHint);
    const updateActions = () => { makeDefault.disabled = !select.value; remove.disabled = !select.value; disabledHint.textContent = select.value ? "" : message("selectTemplateFirst"); };
    if (scope.id === "settingsForm" && state.preferences?.defaultTemplateId) {
      addAction("clearDefaultTemplate", () => ({ action: "default", templateId: null }));
    }
    const reload = element("button", "text-button", message("reloadTemplates")); reload.type = "button"; reload.hidden = true;
    reload.onclick = async () => {
      if (reload.disabled) return; reload.disabled = true;
      try {
        const preferences = await api("/preferences"); if (!isCurrent()) return;
        const selectedId = select.value, draftName = name.value;
        state.preferences = preferences; loadedRevision = preferences.revision;
        renderTemplateControls(scope, selectedId);
        scope.querySelector(".template-name").value = draftName;
        scope.querySelector(".template-editor").open = true;
        scope.querySelector(".template-status").textContent = message("templatesReloaded");
      } catch (error) { if (isCurrent()) status.textContent = errorText(error); }
      finally { reload.disabled = false; }
    };
    editor.append(reload);
    editor.append(controls, element("p", "template-hint", message("templateScopeHint")), status); container.append(editor);
    select.addEventListener("change", () => {
      const config = selected()?.config || state.preferences?.defaults || {};
      for (const [key, value] of Object.entries(config)) {
        const field = scope.querySelector(`[name="${key}"]`);
        if (field && !field.readOnly) field.value = value;
      }
      name.value = selected()?.name || ""; updateActions();
      if (workGroup) updateGroupButtons();
    });
    updateActions();
    UI?.mountControls(container);
    if (workGroup) updateGroupButtons();
  }

  function renderChecks(container, checks) {
    clear(container); container.hidden = !checks?.length;
    for (const check of checks || []) {
      const row = element("div", "check-result");
      const passed = check.ok === true;
      row.append(window.DashboardIcons.icon(passed ? "circle-check" : "circle-alert"));
      row.dataset.state = passed ? "passed" : "failed";
      const body = element("div");
      const key = `check_${check.code || check.name}`;
      const label = window.CENTER_MESSAGES[state.language][key] ? message(key) : check.message || check.label || check.code || message(passed ? "checkPassed" : "checkFailed");
      body.append(element("strong", "", label));
      if (check.code === "FRAMEWORK_UNVERIFIED") body.append(element("p", "", message("frameworkFix")));
      else if (check.detail || check.reason) body.append(element("p", "", check.detail || check.reason));
      row.append(body); container.append(row);
    }
    window.DashboardIcons.hydrate(container);
  }

  function environmentDomain() {
    const form = $("environmentForm");
    const candidate = state.environment?.candidates?.find(item => item.id === form.elements.candidate.value);
    const domain = { ...(candidate?.domain || candidate || {}) };
    delete domain.id; delete domain.label;
    if (domain.platform === "wsl") domain.user = text(form.elements.user.value);
    return domain;
  }
  function selectEnvironment() {
    state.environmentToken += 1;
    const form = $("environmentForm"), domain = environmentDomain();
    $("environmentUserLabel").hidden = domain.platform !== "wsl";
    form.elements.user.required = domain.platform === "wsl";
    renderChecks($("environmentChecks"), []); setFormStatus(form, "");
  }
  async function openEnvironment() {
    openDialog($("environmentDialog"));
    const form = $("environmentForm"), token = ++state.environmentToken;
    const current = () => token === state.environmentToken && $("environmentDialog").open;
    state.environment = null; form.elements.candidate.replaceChildren(); form.elements.user.value = "";
    form.querySelectorAll("button:not(.dialog-close)").forEach(button => { button.disabled = true; });
    renderChecks($("environmentChecks"), []); setFormStatus(form, message("loading"));
    try {
      const value = await api("/environment"); if (!current()) return;
      state.environment = value;
      for (const candidate of value.candidates || []) form.elements.candidate.append(new Option(candidate.label || candidate.id, candidate.id));
      const selected = value.candidates?.find(item => { const domain = item.domain || item; return domain.platform === value.domain?.platform && domain.distribution === value.domain?.distribution; });
      if (selected) form.elements.candidate.value = selected.id;
      form.elements.user.value = value.domain?.user || "";
      $("environmentCurrent").textContent = value.domain ? message("connectedEnvironment", { name: [value.domain.distribution || value.domain.platform, value.domain.user].filter(Boolean).join(" · ") }) : message("environmentNotConnected");
      selectEnvironment(); renderChecks($("environmentChecks"), value.checks);
    } catch (error) { if (current()) { if (error.details?.checks) renderChecks($("environmentChecks"), error.details.checks); setFormStatus(form, errorText(error), true); } }
    finally { if ($( "environmentDialog").open && state.environment) form.querySelectorAll("button:not(.dialog-close)").forEach(button => { button.disabled = !form.elements.candidate.options.length; }); }
  }
  async function environmentAction(action) {
    const form = $("environmentForm"), dialog = $("environmentDialog");
    if (!dialog.open || !state.environment || !form.reportValidity()) return;
    const token = state.environmentToken, dialogToken = state.dialogToken, domain = environmentDomain(), signature = JSON.stringify(domain);
    const current = () => token === state.environmentToken && dialog.open && JSON.stringify(environmentDomain()) === signature;
    const button = action === "check" ? $("environmentCheck") : form.querySelector('[type="submit"]');
    if (!beginSubmission(form, "actionPending", button)) return;
    form.querySelectorAll("button:not(.dialog-close), input, select").forEach(item => { item.disabled = true; });
    try {
      const result = await write(`/environment/${action}`, { domain, expectedRevision: state.environment.revision }, 60000);
      if (action === "connect") { resetImportProbe(); await refresh(); }
      if (!current()) return;
      if (result.revision !== undefined) state.environment.revision = result.revision;
      renderChecks($("environmentChecks"), result.checks);
      setFormStatus(form, message(action === "connect" ? "environmentConnected" : result.ready === false || result.checks?.some(item => item.ok === false) ? "environmentCheckFailed" : "environmentChecked"));
      if (action === "connect") $("environmentCurrent").textContent = message("connectedEnvironment", { name: [domain.distribution || domain.platform, domain.user].filter(Boolean).join(" · ") });
    } catch (error) { if (current()) { if (error.details?.checks) renderChecks($("environmentChecks"), error.details.checks); setFormStatus(form, errorText(error), true); } }
    finally { if (dialog.open && dialogToken === state.dialogToken) { endSubmission(form, button); form.querySelectorAll("button:not(.dialog-close), input, select").forEach(item => { item.disabled = false; }); } }
  }

  async function preparationAction(operation, action) {
    const lock = `operation:${operation.operationId}`; if (state.actionLocks.has(lock)) return;
    const dialogToken = state.dialogToken, drawer = $("queueDrawer");
    state.actionLocks.add(lock); renderQueue();
    try {
      const result = await write(`/operations/${encodeURIComponent(operation.operationId)}/${action}`, { expectedRevision: operation.revision }, 60000);
      if (action === "restore-draft") {
        if (state.dialogToken !== dialogToken || !drawer.open) return;
        restoreWorkDraft(result.draft); closeQueue(); openDialog($("newWorkDialog"));
      } else { showStatus("actionAccepted"); await refresh(); }
    } catch (error) { showStatus("requestFailed", { detail: errorText(error) }, true); }
    finally { state.actionLocks.delete(lock); renderQueue(); }
  }
  function restoreWorkDraft(draft) {
    const form = $("newWorkForm"), groups = $("workGroups"), template = groups.firstElementChild.cloneNode(true);
    form.reset(); groups.replaceChildren();
    for (const saved of draft.groups) {
      const group = template.cloneNode(true); groups.append(group); setupGroup(group);
      for (const [key, value] of Object.entries({ ...saved.config, count: saved.count, direction: saved.direction })) {
        const field = group.querySelector(`[name="${key}"]`); if (field) field.value = value;
      }
    }
    form.elements.executionMode.value = "enqueue";
    selectWorkGroup(groups.firstElementChild); renderChecks($("workChecks"), []);
    setFormStatus(form, message("preparationDraftRestored"));
  }

  async function saveCapacity(event) {
    event.preventDefault(); const form = event.currentTarget;
    const button = form.querySelector('[type="submit"]'); if (!beginSubmission(form, "saving")) return;
    try {
      await write("/queue/capacity", { maxConcurrentProjects: form.elements.unlimited.checked ? null : Number(form.elements.capacity.value), expectedRevision: state.summary?.queueRevision });
      delete form.dataset.dirty; setFormStatus(form, message("capacitySaved")); await refresh();
    } catch (error) { setFormStatus(form, errorText(error), true); }
    finally { endSubmission(form); }
  }

  function workFormContext(form, dialog) {
    const token = state.dialogToken;
    const values = () => JSON.stringify({ config: formConfig(form), mode: form.elements.executionMode.value, direction: form.elements.direction?.value,
      groups: [...form.querySelectorAll(".work-group")].map(group => ({ id: group.id, count: group.querySelector('[name="count"]').value, direction: group.querySelector('[name="direction"]').value, config: formConfig(group) })) });
    const submitted = values();
    return {
      current: () => token === state.dialogToken && dialog.open,
      unchanged: () => token === state.dialogToken && dialog.open && values() === submitted,
      canOpenQueue: () => token === state.dialogToken && !document.querySelector("dialog[open]"),
    };
  }

  async function submitContinue(event) {
    event.preventDefault(); const form = event.currentTarget; const entry = state.activeEntry; const dialog = $("continueDialog"); if (!entry || !dialog.open) return;
    const context = workFormContext(form, dialog);
    if (!beginSubmission(form, form.elements.executionMode.value === "enqueue" ? "submittingQueue" : "submittingStart")) return;
    try {
      await write("/requests", { kind: entry.kind === "exploration" ? "explore" : "continue", entryId: entry.entryId, sourceId: entry.sourceId, runtimeId: entry.runtimeId,
        expectedSourceRevision: entry.sourceRevision, executionMode: form.elements.executionMode.value, config: formConfig(form) });
      const completedCurrentForm = context.unchanged();
      if (completedCurrentForm) closeDialog(dialog);
      showStatus("requestCreated"); await refresh();
      if (completedCurrentForm && context.canOpenQueue()) openQueue();
    } catch (error) { if (context.unchanged()) setFormStatus(form, message("requestFailed", { detail: errorText(error) }), true); }
    finally { if (context.current()) { if (!context.unchanged()) setFormStatus(form, ""); endSubmission(form); form.querySelector('[type="submit"]').disabled = !capability(entry, "execute").enabled || state.stale; } }
  }

  async function submitNewWork(event) {
    event.preventDefault(); const form = event.currentTarget; const dialog = $("newWorkDialog"); if (!dialog.open) return;
    const context = workFormContext(form, dialog);
    if (!beginSubmission(form, form.elements.executionMode.value === "enqueue" ? "submittingQueue" : "submittingStart")) return;
    state.workSubmitting = true;
    try {
      const groups = [...form.querySelectorAll(".work-group")].map((group) => ({ count: Number(group.querySelector('[name="count"]').value), direction: text(group.querySelector('[name="direction"]').value), config: formConfig(group) }));
      setFormStatus(form, message("preflightPending"));
      const checked = await write("/preflight", { groups }, 60000);
      if (!context.unchanged()) return;
      renderChecks($("workChecks"), checked.checks);
      if (!checked.ready) { setFormStatus(form, message("preflightFailed"), true); return; }
      const batch = await write("/explorations/batch", { groups, executionMode: form.elements.executionMode.value, environmentRevision: checked.environmentRevision }, 60000);
      for (const operation of batch.items || []) state.operations = [operation, ...state.operations.filter((item) => item.operationId !== operation.operationId)];
      const completedCurrentForm = context.unchanged();
      if (completedCurrentForm) closeDialog(dialog);
      const items = batch.items || [], failed = items.filter(item => ["failed", "attention"].includes(item.state)).length;
      if (failed) showStatus("batchPartial", { total: items.length, failed, success: items.filter(item => item.state === "succeeded").length, pending: items.filter(item => item.state === "preparing").length }, true);
      else showStatus("explorationPrepared");
      await refresh();
      if (completedCurrentForm && context.canOpenQueue()) openQueue();
    } catch (error) { if (context.unchanged()) setFormStatus(form, message("requestFailed", { detail: errorText(error) }), true); }
    finally { if (context.current()) { state.workSubmitting = false; if (!context.unchanged()) setFormStatus(form, ""); endSubmission(form); updateGroupButtons(); } }
  }

  function renderProbe(candidate) {
    const container = clear($("probeResult")); container.hidden = false;
    const list = element("dl");
    const items = Array.isArray(candidate.items) ? candidate.items : [candidate];
    const names = items.map((item) => text(item.displayName || item.name)).filter(Boolean).join(" · ") || message("probeNoName");
    const kinds = [...new Set(items.map((item) => text(item.kind)).filter(Boolean))].map((kind) => window.CENTER_MESSAGES[state.language][`kind_${kind}`] ? message(`kind_${kind}`) : kind).join(" · ") || message("notRecorded");
    for (const [label, value] of [[message("probeName"), names], [message("probeKind"), kinds], [message("probeCapabilities"), message("readOnly")], [message("probeWarnings"), (candidate.warnings || []).join(" · ") || message("notRecorded")]]) {
      list.append(element("dt", "", label), element("dd", "", String(value)));
    }
    container.append(list);
  }

  async function submitProbe(event) {
    event.preventDefault(); const form = event.currentTarget; resetImportProbe();
    const token = state.probeToken; const root = text(form.elements.root.value); const mode = form.elements.mode.value;
    const isCurrent = () => token === state.probeToken && $("importDialog").open && root === text(form.elements.root.value) && mode === form.elements.mode.value;
    if (!beginSubmission(form, "probing")) return;
    try {
      const candidate = await write("/imports/probe", { root, ...(mode === "reference" ? { kindHint: "reference" } : {}) }, 60000);
      if (!isCurrent()) return;
      if (!candidate?.candidateId || !candidate?.candidateHash) throw new APIError({ code: "INVALID_RESPONSE" }, 200);
      state.probe = candidate; renderProbe(candidate); $("commitImportButton").hidden = false; setFormStatus(form, message("probeReady"));
    } catch (error) { if (isCurrent()) setFormStatus(form, message("requestFailed", { detail: errorText(error) }), true); }
    finally { if (isCurrent()) endSubmission(form); }
  }

  async function commitImport() {
    const form = $("importForm"); const dialog = $("importDialog"); const button = $("commitImportButton");
    if (!state.probe || !dialog.open || button.disabled) return;
    const probe = state.probe; const token = state.probeToken;
    const isCurrent = () => token === state.probeToken && state.probe === probe && dialog.open;
    if (!beginSubmission(form, "actionPending", button)) return;
    $("probeButton").disabled = true;
    try {
      const imported = await write("/imports/commit", { candidateId: probe.candidateId, candidateHash: probe.candidateHash, mode: form.elements.mode.value === "reference" ? "reference" : "readonly", expectedRevision: state.apiRevision ?? state.revision }, 60000);
      if (isCurrent()) closeDialog(dialog);
      if (form.elements.mode.value === "reference") state.filter = "reference";
      showStatus("importComplete"); await refresh();
    } catch (error) { if (isCurrent()) setFormStatus(form, message("requestFailed", { detail: errorText(error) }), true); }
    finally { if (isCurrent()) { endSubmission(form, button); $("probeButton").disabled = false; } }
  }

  function sourceStatus(value, error = false) {
    const node = $("sourceManagerStatus"); node.textContent = value; node.classList.toggle("error", error);
    return ++state.sourceStatusToken;
  }

  async function waitOperation(operation) {
    if (!operation?.operationId || !["running", "preparing"].includes(operation.state)) return operation;
    for (let attempt = 0; attempt < 60; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      operation = await api(`/operations/${encodeURIComponent(operation.operationId)}`);
      if (!["running", "preparing"].includes(operation.state)) return operation;
    }
    throw new APIError({ code: "CONTEXT_UNAVAILABLE", messageKey: "operationInProgress" }, 408);
  }

  function sourceContext() {
    const token = state.sourceToken; const entryId = state.managementEntry?.entryId; const sourceId = state.selectedSourceId;
    return () => token === state.sourceToken && $("sourceDialog").open && entryId === state.managementEntry?.entryId && sourceId === state.selectedSourceId;
  }

  async function refreshSourceManager(successKey, isCurrent = sourceContext()) {
    try {
      const entryId = state.managementEntry?.entryId; if (!entryId || !isCurrent()) return;
      const token = ++state.sourceRefreshToken;
      let detail;
      try { detail = await api(`/entries/${encodeURIComponent(entryId)}`); }
      catch (error) {
        if (!isCurrent() || token !== state.sourceRefreshToken) return;
        throw error;
      }
      if (!isCurrent() || token !== state.sourceRefreshToken) return;
      state.managementEntry = detail;
      state.selectedSourceId = detail.sourceId;
      renderSourceManager(); sourceStatus(message(successKey));
    } finally { await refresh(); }
  }

  async function sourceOperation(path, body, successKey = "managementComplete") {
    const isCurrent = sourceContext();
    sourceStatus(message("operationInProgress"));
    try {
      const operation = await waitOperation(await write(path, body, 60000));
      if (!isCurrent()) { await refresh(); return; }
      if (["attention", "failed"].includes(operation?.state)) { sourceStatus(message("operationAttention", { reason: capabilityReason(operation.reason || "CONTEXT_UNAVAILABLE") }), true); return; }
      await refreshSourceManager(successKey, isCurrent);
    } catch (error) { if (isCurrent()) sourceStatus(message("requestFailed", { detail: errorText(error) }), true); }
  }

  function syncSourceActions() {
    const busy = $("sourceManagerBody").dataset.submitting === "true";
    for (const { button, hint, enabled, reason } of state.sourceActions) {
      button.disabled = busy || !enabled;
      hint.textContent = busy && enabled ? message("operationInProgress") : enabled ? "" : capabilityReason(reason);
    }
  }

  function managementAction(container, labelKey, enabled, reason, action, danger = false) {
    const row = element("div", "management-action");
    const button = element("button", `button ${danger ? "danger" : "secondary"}`, message(labelKey)); button.type = "button"; button.disabled = !enabled;
    if (enabled) button.addEventListener("click", async () => {
      const scope = $("sourceManagerBody"); if (scope.dataset.submitting === "true") { sourceStatus(message("operationInProgress")); return; }
      scope.dataset.submitting = "true"; scope.setAttribute("aria-busy", "true");
      const focusedOnStart = document.activeElement === button;
      syncSourceActions();
      const label = button.textContent; button.textContent = message("actionPending");
      try { await action(); }
      finally { delete scope.dataset.submitting; scope.removeAttribute("aria-busy"); syncSourceActions(); if (button.isConnected) { button.textContent = label; if (focusedOnStart && (document.activeElement === document.body || document.activeElement?.dataset.dialogId === "sourceDialog") && $("sourceDialog").open) focusControl(button); } }
    });
    const hint = element("small");
    state.sourceActions.push({ button, hint, enabled, reason }); syncSourceActions();
    row.append(button, hint);
    container.append(row);
  }

  function renderSourceManager() {
    const entry = state.managementEntry; const body = clear($("sourceManagerBody")); state.sourceActions = []; if (!entry) return;
    const isCurrent = sourceContext();
    const sources = Array.isArray(entry.sources) ? entry.sources : [];
    if (!sources.length) { body.append(element("p", "list-state", message("noSources"))); return; }
    const fieldset = element("fieldset", "source-list"); fieldset.append(element("legend", "visually-hidden", message("sourceList")));
    sources.forEach((source, index) => {
      const label = element("label", "source-choice"); const input = document.createElement("input"); input.type = "radio"; input.name = "managedSource"; input.value = source.sourceId;
      input.checked = source.sourceId === state.selectedSourceId; input.addEventListener("change", () => { state.sourceToken += 1; state.selectedSourceId = source.sourceId; sourceStatus(""); renderSourceManager(); });
      const title = text(source.displayName || source.rootName) || source.project || message("sourceNumber", { number: index + 1 });
      const detail = [message(`kind_${source.kind}`), source.sourceId === entry.sourceId ? message("currentSource") : "", statusLabel(source.availability === "available" ? "read_only" : "unknown"), source.project && source.project !== title ? message("sourceProject", { project: source.project }) : "", message("sourceIdShort", { id: source.sourceId.slice(-8) })].filter(Boolean).join(" · ");
      label.append(input, element("strong", "", title), element("small", "", detail)); fieldset.append(label);
    });
    body.append(fieldset);
    const source = sources.find((item) => item.sourceId === state.selectedSourceId) || sources[0]; const current = source.sourceId === entry.sourceId;
    const diagnostics = element("details", "source-diagnostics"); diagnostics.append(element("summary", "", message("sourceDetails")));
    const diagnosticRows = [[message("sourceIdentifier"), source.sourceId], [message("sourceProjectLabel"), source.project], [message("sourceLocation"), source.displayPath], [message("sourceLastVerified"), source.lastVerifiedAt ? formatTime(source.lastVerifiedAt) : message("notRecorded")]].filter(([, value]) => text(value));
    const diagnosticList = element("dl"); for (const [label, value] of diagnosticRows) diagnosticList.append(element("dt", "", label), element("dd", "", value)); diagnostics.append(diagnosticList); body.append(diagnostics);
    const documents = Array.isArray(source.registeredDocuments) ? source.registeredDocuments : [];
    if (documents.length) {
      const section = element("div", "source-documents"); section.append(element("strong", "", message("registeredDocuments")));
      for (const document of documents) { const link = element("a", "", document.label || document.path || message("view")); link.href = `${API}/entries/${encodeURIComponent(entry.entryId)}/resources/${encodeURIComponent(document.id)}?sourceId=${encodeURIComponent(source.sourceId)}`; link.target = "_blank"; link.rel = "noopener"; section.append(link); }
      body.append(section);
    }
    const reconnect = element("label", "reconnect-field"); reconnect.append(element("span", "", message("reconnectPath")));
    const root = element("input"); root.type = "text"; root.autocomplete = "off"; root.spellcheck = false; root.placeholder = message("folderPlaceholder"); reconnect.append(root, element("small", "", message("reconnectHint"))); body.append(reconnect);
    let reconnectToken = 0; let reconnectStatusToken = null;
    root.addEventListener("input", () => {
      reconnectToken += 1;
      if (reconnectStatusToken === state.sourceStatusToken) sourceStatus("");
    });
    const actions = element("div", "management-actions"); const takeover = capability(entry, "takeover"); const release = capability(entry, "release"); const preview = capability(entry, "preview"); const previewStop = capability(entry, "previewStop"); const capture = capability(entry, "capture");
    managementAction(actions, "selectSource", !current, current ? "UNSUPPORTED" : "", async () => {
      sourceStatus(message("actionPending")); try { await write(`/entries/${encodeURIComponent(entry.entryId)}/source-selection`, { sourceId: source.sourceId, expectedRevision: entry.revision }); await refreshSourceManager("sourceSelected", isCurrent); } catch (error) { if (isCurrent()) sourceStatus(message("requestFailed", { detail: errorText(error) }), true); }
    });
    const recovery = capability(entry, "reviewRecovery");
    for (const lockOnly of [false, true]) {
      const allowed = lockOnly ? capability(entry, "reviewProductLock").enabled || entry.recovery?.canReviewLock : recovery.enabled || entry.recovery?.canReview;
      if (!current || !allowed) continue;
      managementAction(actions, lockOnly ? "reviewProductLock" : "reviewRecovery", !state.stale, "", async () => {
        sourceStatus(message("actionPending"));
        const request = { expectedRevision: source.revision, expectedSourceRevision: source.sourceRevision };
        try {
          const review = await write(`/sources/${encodeURIComponent(source.sourceId)}/${lockOnly ? "review-product-lock" : "review-recovery"}`, request, 60000);
          if (review.expectedRevision !== undefined) request.expectedRevision = review.expectedRevision;
          if (review.expectedSourceRevision !== undefined) request.expectedSourceRevision = review.expectedSourceRevision;
          if (!isCurrent()) return;
          body.querySelector(".recovery-review")?.remove();
          const panel = element("section", "recovery-review");
          panel.append(element("h3", "", message("recoveryReview")));
          const checks = element("div", "check-results"); renderChecks(checks, review.checks); panel.append(checks);
          for (const reason of review.reasons || []) panel.append(element("p", "", capabilityReason(typeof reason === "string" ? reason : reason.message || reason.code)));
          const lock = review.canRecoverLock === true;
          if (review.canConfirm || lock) {
            const fields = lock ? [["confirmAllWritersStopped", "confirmWritersStopped"], ["confirmLockRecoveryScope", "confirmLockScope"]]
              : [["confirmCodeEffects", "confirmCodeEffects"], ["confirmExternalEffects", "confirmExternalEffects"]];
            const acknowledgements = [];
            for (const [name, key] of fields) {
              const label = element("label", "radio-row"), input = element("input"); input.type = "checkbox"; input.name = name;
              label.append(input, element("span", "", message(key))); panel.append(label); acknowledgements.push(input);
            }
            const confirm = element("button", "button secondary", message(lock ? "recoverLock" : "confirmRecovery")); confirm.type = "button"; confirm.disabled = true;
            const update = () => { confirm.disabled = !acknowledgements.every(input => input.checked) || state.stale; };
            acknowledgements.forEach(input => input.addEventListener("change", update));
            confirm.onclick = async () => {
              const owner = $("sourceManagerBody"); if (!isCurrent() || owner.dataset.submitting === "true") return;
              owner.dataset.submitting = "true"; syncSourceActions(); confirm.disabled = true;
              try {
                await write(`/sources/${encodeURIComponent(source.sourceId)}/${lock ? "confirm-product-lock" : "confirm-recovery"}`, { ...request,
                  ...(lock ? { lockReviewToken: review.lockReviewToken } : { reviewToken: review.reviewToken }),
                  ...Object.fromEntries(acknowledgements.map(input => [input.name, input.checked])) }, 60000);
                await refreshSourceManager(lock ? "lockRecovered" : "recoveryConfirmed", isCurrent);
              } catch (error) { if (isCurrent()) sourceStatus(errorText(error), true); }
              finally { delete owner.dataset.submitting; syncSourceActions(); if (isCurrent()) update(); }
            };
            panel.append(confirm);
          }
          body.append(panel); UI.mountControls(panel); sourceStatus(message("recoveryNotStarted"));
        } catch (error) { if (isCurrent()) sourceStatus(errorText(error), true); }
      });
    }
    const sourceRevision = source.revision;
    managementAction(actions, "reconnectSource", current && !release.enabled, !current ? "selectCurrentFirst" : release.enabled ? "releaseFirst" : "", async () => {
      if (!text(root.value)) { reconnectStatusToken = sourceStatus(message("requestFailed", { detail: message("folderPath") }), true); root.focus(); return; }
      const token = reconnectToken; const isReconnectCurrent = () => isCurrent() && token === reconnectToken;
      reconnectStatusToken = sourceStatus(message("probing"));
      try {
        const candidate = await write("/imports/probe", { root: text(root.value) }, 60000);
        if (!isReconnectCurrent()) return;
        await write(`/sources/${encodeURIComponent(source.sourceId)}/reconnect`, { candidateId: candidate.candidateId, candidateHash: candidate.candidateHash, expectedRevision: sourceRevision }, 60000);
        await refreshSourceManager("sourceReconnected", isReconnectCurrent);
      } catch (error) { if (isReconnectCurrent()) reconnectStatusToken = sourceStatus(message("requestFailed", { detail: errorText(error) }), true); }
    });
    managementAction(actions, "takeover", current && takeover.enabled, !current ? "selectCurrentFirst" : takeover.reason, () => sourceOperation(`/sources/${encodeURIComponent(source.sourceId)}/takeover`, { expectedRevision: sourceRevision }));
    managementAction(actions, "release", current && release.enabled, !current ? "selectCurrentFirst" : release.reason, () => sourceOperation(`/sources/${encodeURIComponent(source.sourceId)}/release`, { expectedRevision: sourceRevision }));
    managementAction(actions, "previewStart", current && preview.enabled, !current ? "selectCurrentFirst" : preview.reason, () => sourceOperation(`/entries/${encodeURIComponent(entry.entryId)}/preview/start`, { sourceId: source.sourceId, expectedRevision: sourceRevision }));
    managementAction(actions, "previewStop", current && previewStop.enabled, !current ? "selectCurrentFirst" : previewStop.reason, () => sourceOperation(`/entries/${encodeURIComponent(entry.entryId)}/preview/stop`, { sourceId: source.sourceId, expectedRevision: sourceRevision }));
    managementAction(actions, "captureMedia", current && capture.enabled, !current ? "selectCurrentFirst" : capture.reason, () => sourceOperation(`/entries/${encodeURIComponent(entry.entryId)}/media/capture`, { sourceId: source.sourceId, expectedRevision: sourceRevision }));
    managementAction(actions, "detachEntry", current && !release.enabled, !current ? "selectCurrentFirst" : release.enabled ? "releaseFirst" : "", () => { closeDialog($("sourceDialog")); confirmReferenceDetach(entry); }, true);
    body.append(actions);
    UI?.mountControls(body);
  }

  async function openSourceManager(entry) {
    const token = ++state.sourceToken; state.managementEntry = null; state.selectedSourceId = null; $("sourceProduct").textContent = entry.displayName || message("fieldMissing"); clear($("sourceManagerBody")); sourceStatus(message("loading")); openDialog($("sourceDialog"));
    try { const detail = await api(`/entries/${encodeURIComponent(entry.entryId)}`); if (token !== state.sourceToken || !$("sourceDialog").open) return; state.managementEntry = detail; state.selectedSourceId = detail.sourceId; renderSourceManager(); sourceStatus(""); }
    catch (error) { if (token === state.sourceToken && $("sourceDialog").open) sourceStatus(message("requestFailed", { detail: errorText(error) }), true); }
  }

  function setPreferenceFieldsDisabled(form, disabled) {
    for (const name of ["language", "engine", "model", "effort", "productLanguage"]) form.elements[name].disabled = disabled;
    const templates = form.querySelector(".template-controls");
    if (templates) templates.hidden = disabled;
  }

  async function loadPreferences() {
    const token = ++state.preferencesToken; state.preferencesRevision = null;
    const form = $("settingsForm"); const button = form.querySelector('[type="submit"]'); button.disabled = true; setPreferenceFieldsDisabled(form, true); setFormStatus(form, message("loading"));
    const isCurrent = () => token === state.preferencesToken && $("settingsDialog").open;
    try {
      const preferences = await api("/preferences");
      if (!isCurrent()) return;
      if (!Number.isSafeInteger(preferences?.revision) || preferences.revision < 0) throw new APIError({ code: "INVALID_RESPONSE" }, 200);
      state.preferences = preferences;
      // The expected revision belongs to the values loaded into this form.
      // Background polling may update defaults, but cannot renew this edit's lease.
      state.preferencesRevision = preferences.revision;
      form.elements.language.value = preferences.language || state.language;
      fillDefaults(form); renderTemplateControls(form); $("defaultsTemplateHint").hidden = !state.preferences.defaultTemplateId; setFormStatus(form, ""); setPreferenceFieldsDisabled(form, false); button.disabled = false;
    } catch (error) { if (isCurrent()) setFormStatus(form, message("requestFailed", { detail: errorText(error) }), true); }
  }

  async function savePreferences(event) {
    event.preventDefault(); const form = event.currentTarget; const button = form.querySelector('[type="submit"]');
    if (button.disabled || state.preferencesRevision === null || !$("settingsDialog").open) return;
    const token = state.preferencesToken; const isCurrent = () => token === state.preferencesToken && $("settingsDialog").open;
    const values = () => ({ language: form.elements.language.value, ...formConfig(form) });
    const submitted = values();
    if (!beginSubmission(form, "saving")) return;
    try {
      const preferences = await write("/preferences", { preferences: submitted, expectedRevision: state.preferencesRevision });
      if (!Number.isSafeInteger(preferences?.revision) || preferences.revision < 0) throw new APIError({ code: "INVALID_RESPONSE" }, 200);
      if (isCurrent()) {
        const unchanged = JSON.stringify(values()) === JSON.stringify(submitted);
        state.preferences = preferences; state.language = preferences.language;
        // Only this successful write can advance the preserved edit's lease.
        state.preferencesRevision = preferences.revision;
        if (unchanged) closeDialog($("settingsDialog"));
        else setFormStatus(form, message("preferencesNewerEdits"));
        renderPage();
        if (unchanged) showStatus("preferencesSaved");
      }
      await refresh();
    } catch (error) { if (isCurrent()) setFormStatus(form, message("requestFailed", { detail: errorText(error) }), true); }
    finally { if (isCurrent()) endSubmission(form); }
  }

  function entryIdentity(entry) { return `${entry.displayName || message("fieldMissing")} · ${entry.shortId || entry.entryId.slice(-8)}`; }
  function managementDialog(title, build) {
    $("managementTitle").textContent = title; clear($("managementBody")); $("managementStatus").textContent = "";
    build($("managementBody")); openDialog($("managementDialog"));
  }
  function renameEntry(entry) {
    managementDialog(message("rename"), body => {
      const form = element("form", "group-editor"), label = element("label", "", message("productName")), input = element("input");
      input.value = entry.displayName || ""; input.required = true; input.maxLength = 80; label.append(input);
      const save = element("button", "button primary", message("save")); save.type = "submit"; form.append(label, save); body.append(form);
      form.onsubmit = async event => {
        event.preventDefault(); save.disabled = true; form.setAttribute("aria-busy", "true"); $("managementStatus").textContent = message("saving");
        try {
          await write(`/entries/${encodeURIComponent(entry.entryId)}/rename`, { displayName: input.value, expectedRevision: entry.revision ?? state.revision });
          await refresh(); closeDialog($("managementDialog"));
        } catch (error) { $("managementStatus").textContent = errorText(error); }
        finally { save.disabled = false; form.removeAttribute("aria-busy"); }
      };
    });
  }
  function trashEntryAction(entry, action) {
    confirmAction(action === "delete" ? "deletePermanently" : action === "restore-trash" ? "restoreTrash" : "moveToTrash",
      action === "delete" ? "deleteMessage" : action === "restore-trash" ? "restoreTrashMessage" : "trashMessage",
      async () => {
        const payload = { expectedRevision: entry.revision ?? state.revision };
        if (action === "trash") payload.confirm = true;
        if (action === "delete") payload.confirmPermanent = true;
        await write(`/entries/${encodeURIComponent(entry.entryId)}/${action}`, payload, action === "delete" ? 300000 : 30000);
        await refresh();
      },
      action !== "restore-trash", entryIdentity(entry),
      action === "delete" ? "deletePermanently" : action === "restore-trash" ? "restoreTrash" : "confirmTrash");
  }
  function trashSettings() {
    const openedCenterId = state.centerId;
    let openedRevision = state.trash?.revision ?? 1;
    const openedDays = state.trash?.retentionDays ?? 30;
    managementDialog(message("trashSettings"), body => {
      body.append(element("p", "", message("trashRetentionIntro")));
      const form = element("form", "group-editor"), label = element("label", "", message("retentionDays")), input = element("input");
      input.type = "number"; input.min = 1; input.max = 3650; input.value = openedDays; input.required = true; label.append(input);
      const save = element("button", "button primary", message("save")); save.type = "submit"; form.append(label, save); body.append(form);
      form.onsubmit = async event => {
        event.preventDefault();
        if (state.centerId !== openedCenterId) { $("managementStatus").textContent = message("staleData"); return; }
        save.disabled = true; $("managementStatus").textContent = message("saving");
        try {
          await write("/trash/settings", { retentionDays: Number(input.value), expectedRevision: openedRevision, expectedCenterId: openedCenterId });
          await refresh(); closeDialog($("managementDialog"));
        } catch (error) {
          if (error?.code === "REVISION_CONFLICT") {
            await Promise.allSettled([refresh(), readPart("trash", "/trash")]);
            openedRevision = state.trash?.revision ?? openedRevision;
            input.value = state.trash?.retentionDays ?? input.value;
          }
          $("managementStatus").textContent = errorText(error);
        }
        finally { save.disabled = false; }
      };
    });
  }

  function confirmAction(titleKey, messageKey, action, danger = false, name = "", actionKey = titleKey) {
    state.confirmAction = action; endSubmission($("confirmForm")); $("confirmActionButton").disabled = false; $("confirmTitle").textContent = message(titleKey); $("confirmMessage").textContent = `${name ? `${message("objectConfirmation", { name })} · ` : ""}${message(messageKey)}`;
    $("confirmActionButton").textContent = message(actionKey); delete $("confirmActionButton").dataset.i18n;
    $("confirmActionButton").classList.toggle("primary", !danger); $("confirmActionButton").classList.toggle("danger", danger);
    $("confirmActionButton").className = element("button", danger ? "button danger" : "button primary").className;
    $("confirmActionButton").dataset.variant = danger ? "destructive" : "default";
    setFormStatus($("confirmForm"), ""); openDialog($("confirmDialog"));
  }

  function confirmEntryVisibility(entry) {
    const action = entry.archived ? "restore" : "archive";
    confirmAction(`${action}Title`, `${action}Message`, async () => {
      await write(`/entries/${encodeURIComponent(entry.entryId)}/${action}`, { expectedRevision: entry.revision ?? state.apiRevision ?? state.revision });
      showStatus(entry.archived ? "restoreSuccess" : "archiveSuccess"); await refresh();
    }, false, entry.displayName || message("fieldMissing"), action);
  }

  function confirmReferenceDetach(entry) {
    const reference = entry.kind === "reference";
    confirmAction(reference ? "detachReferenceTitle" : "detachEntryTitle", reference ? "detachReferenceMessage" : "detachEntryMessage", async () => {
      await write(`/entries/${encodeURIComponent(entry.entryId)}/detach`, { expectedRevision: entry.revision ?? state.apiRevision ?? state.revision });
      showStatus(reference ? "detachReferenceSuccess" : "detachEntrySuccess"); await refresh();
    }, true, entry.displayName || message("fieldMissing"), reference ? "detachReference" : "detachEntry");
  }

  function confirmRequestAction(request, action) {
    confirmAction(action === "stop" ? "stopTitle" : "cancelTitle", action === "stop" ? "stopMessage" : "cancelMessage", () => runRequestAction(request, action, true), action === "stop", request.displayName || message(`kind_${request.kind}`), action === "stop" ? "stopItem" : "confirmCancelRequest");
  }

  async function runRequestAction(request, action, propagate = false) {
    const lock = `request:${request.requestId}`;
    const settle = async (pending) => {
      try { return await pending; }
      catch (error) { if (propagate) throw error; showStatus("requestFailed", { detail: errorText(error) }, true); }
    };
    const current = state.requestActions.get(lock);
    if (current && current.action === action) return settle(current.promise);
    if (state.actionLocks.has(lock)) return settle(Promise.reject(new APIError({ code: "ACTION_IN_PROGRESS", messageKey: "operationInProgress" }, 409)));
    state.actionLocks.add(lock);
    const controls = [...document.querySelectorAll("[data-focus-key]")].filter(node => node.dataset.focusKey.startsWith(`${lock}:`)); controls.forEach(node => { node.disabled = true; });
    const pending = (async () => {
      try {
        const body = action === "stop" ? { expectedDispatchId: request.dispatchId } : { expectedRevision: request.revision ?? state.revision };
        await write(`/requests/${encodeURIComponent(request.requestId)}/${action}`, body, action === "stop" ? 60000 : 30000);
        showStatus("actionAccepted"); await refresh();
      }
      finally { state.actionLocks.delete(lock); queueNodes.delete(request.requestId); queueSignature = ""; const focused = rememberFocus(); renderQueue(); restoreFocus(focused); }
    })();
    const operation = { action, promise: pending };
    state.requestActions.set(lock, operation);
    try { return await settle(pending); }
    finally { if (state.requestActions.get(lock) === operation) state.requestActions.delete(lock); }
  }

  async function moveRequest(index, offset, queued) {
    if (state.actionLocks.has("queue-order")) return; state.actionLocks.add("queue-order");
    const reordered = [...queued]; const [item] = reordered.splice(index, 1); reordered.splice(index + offset, 0, item);
    try {
      await write("/queue/order", { requestIds: reordered.map((request) => request.requestId), expectedRevision: state.summary?.queueRevision });
      showStatus("queueChanged"); await refresh();
    } catch (error) { showStatus("requestFailed", { detail: errorText(error) }, true); }
    finally { state.actionLocks.delete("queue-order"); }
  }

  async function toggleDispatch() {
    if (state.actionLocks.has("dispatch")) return; state.actionLocks.add("dispatch");
    const action = state.summary?.dispatchEnabled === true ? "pause" : "resume";
    $("dispatchButton").disabled = true;
    try { await write(`/queue/${action}`, { expectedRevision: state.summary?.queueRevision }); showStatus("actionAccepted"); await refresh(); }
    catch (error) { showStatus("requestFailed", { detail: errorText(error) }, true); }
    finally { state.actionLocks.delete("dispatch"); renderQueue(); }
  }

  function openQueue() {
    state.drawerOpen = true;
    $("queueNavButton").setAttribute("aria-expanded", "true");
    $("queueDrawer").showModal();
    $("capacityForm").querySelectorAll('[type="submit"]').forEach(reserveSubmissionWidth);
  }

  function closeQueue() { $("queueDrawer").close(); }

  function clearFilters() { state.filter = "all"; state.roundFilter = "all"; state.query = ""; $("productSearch").value = ""; renderPage(); }

  function resetImportProbe() {
    endSubmission($("importForm")); state.probeToken += 1; state.probe = null; $("probeButton").disabled = false; $("probeResult").hidden = true; $("commitImportButton").hidden = true; $("commitImportButton").disabled = false; setFormStatus($("importForm"), "");
  }

  function wire() {
    state.loadStarted = performance.now();
    view.listen(window, "dashboard:environment", openEnvironment);
    $("environmentForm").addEventListener("submit", event => { event.preventDefault(); environmentAction("connect"); });
    $("environmentCheck").addEventListener("click", () => environmentAction("check"));
    $("environmentForm").elements.candidate.addEventListener("change", selectEnvironment);
    $("environmentForm").elements.user.addEventListener("input", selectEnvironment);
    $("environmentDialog").addEventListener("close", () => { ++state.environmentToken; });
    $("queueNavButton").addEventListener("click", openQueue); $("closeQueueButton").addEventListener("click", closeQueue);
    $("queueDrawer").addEventListener("close", () => { state.drawerOpen = false; $("queueNavButton").setAttribute("aria-expanded", "false"); });
    $("dispatchButton").addEventListener("click", toggleDispatch);
    $("stopAllButton").addEventListener("click", () => {
      const groups = queueGroups();
      const names = [...groups.running, ...groups.queued, ...groups.attention.filter(requestOwnsDispatch)].map(request => text(request.displayName) || message(`kind_${request.kind}`));
      if (groups.preparing.length) names.push(`${message("preparationItem")} × ${groups.preparing.length}`);
      confirmAction("stopAllTitle", "stopAllMessage", async () => { await write("/queue/stop-all", { expectedRevision: state.summary?.queueRevision }, 60000); showStatus("actionAccepted"); await refresh(); }, true, names.join(" · "), "stopAll");
    });
    $("queueHistoryButton").addEventListener("click", () => { state.historyVisible = !state.historyVisible; renderQueue(); });
    $("newWorkButton").addEventListener("click", () => { if ($("newWorkDialog").closest("[data-motion-exit]")) { $("newWorkDialog").showModal(); return; } const form = $("newWorkForm"); renderChecks($("workChecks"), []); form.reset(); while ($("workGroups").children.length > 1) $("workGroups").lastElementChild.remove(); setupGroup($("workGroups").firstElementChild); setFormStatus(form, ""); openDialog($("newWorkDialog")); });
    $("importButton").addEventListener("click", () => { if ($("importDialog").closest("[data-motion-exit]")) { $("importDialog").showModal(); return; } const form = $("importForm"); form.reset(); resetImportProbe(); openDialog($("importDialog")); });
    $("trashSettingsButton").addEventListener("click", trashSettings);
    $("settingsButton").addEventListener("click", () => {
      const dialog = $("settingsDialog");
      const resuming = dialog.open || Boolean(dialog.closest('[data-motion-exit]'));
      openDialog(dialog); if (!resuming) loadPreferences();
    });
    $("centerAutoRefresh").addEventListener("change", event => {
      state.autoRefresh = event.target.checked; clearTimeout(state.timer);
      try { window.localStorage?.setItem("autonomous-company:center:auto-refresh", state.autoRefresh ? "on" : "off"); } catch (_) {}
      if (state.autoRefresh) refresh();
    });
    $("centerRefreshButton").addEventListener("click", async event => { const button = event.currentTarget; if (button.disabled) return; button.disabled = true; button.setAttribute("aria-busy", "true"); button.textContent = message("loading"); try { await refresh(); } finally { button.disabled = false; button.removeAttribute("aria-busy"); button.textContent = message("retryRead"); } });
    $("addWorkGroup").addEventListener("click", () => {
      const group = $("workGroups").firstElementChild.cloneNode(true);
      $("workGroups").append(group); setupGroup(group);
      group.querySelector("input, select")?.focus();
    });
    $("newWorkForm").addEventListener("invalid", (event) => {
      const group = event.target.closest(".work-group"); if (group) selectWorkGroup(group);
    }, true);
    $("newWorkForm").addEventListener("change", (event) => { if (event.target.name === "executionMode") updateGroupButtons(); });
    $("capacityForm").addEventListener("input", event => { event.currentTarget.dataset.dirty = "true"; });
    $("capacityForm").addEventListener("change", (event) => {
      const form = event.currentTarget; form.dataset.dirty = "true";
      form.elements.capacity.disabled = form.elements.unlimited.checked;
    });
    $("capacityForm").addEventListener("submit", saveCapacity);
    $("newWorkForm").addEventListener("submit", submitNewWork); $("continueForm").addEventListener("submit", submitContinue); $("importForm").addEventListener("submit", submitProbe); $("commitImportButton").addEventListener("click", commitImport); $("settingsForm").addEventListener("submit", savePreferences);
    Array.from($("importForm").elements.mode).forEach((control) => control.addEventListener("change", resetImportProbe));
    $("importForm").elements.root.addEventListener("input", resetImportProbe);
    $("importDialog").addEventListener("cancel", resetImportProbe);
    $("importDialog").addEventListener("close", () => { if (!$("importDialog").open) resetImportProbe(); });
    $("confirmForm").addEventListener("submit", async (event) => {
      event.preventDefault(); const action = state.confirmAction; const button = $("confirmActionButton"); const dialog = $("confirmDialog");
      if (!action || button.disabled || !dialog.open) return;
      const isCurrent = () => state.confirmAction === action && dialog.open;
      if (!beginSubmission($("confirmForm"))) return;
      try { await action(); if (isCurrent()) { state.confirmAction = null; closeDialog(dialog); } }
      catch (error) { if (isCurrent()) setFormStatus($("confirmForm"), message("requestFailed", { detail: errorText(error) }), true); }
      finally { if (isCurrent()) endSubmission($("confirmForm")); }
    });
    document.querySelectorAll(".dialog-close").forEach((button) => button.addEventListener("click", () => closeDialog(button.closest("[data-dialog-id]"))));
    document.querySelectorAll("dialog").forEach((dialog) => dialog.addEventListener("click", (event) => { if (event.target !== dialog) return; const box = dialog.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) closeDialog(dialog); }));
    document.querySelectorAll(".filter-button").forEach((button) => button.addEventListener("click", () => { state.filter = button.dataset.filter; saveView(); renderPage(); }));
    document.querySelectorAll("[data-filter-target]").forEach((button) => button.addEventListener("click", () => { state.filter = button.dataset.filterTarget; saveView(); renderPage(); $("catalogHeading").scrollIntoView({ behavior: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" }); }));
    let searchTimer; $("productSearch").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { state.query = $("productSearch").value.trim(); saveView(); renderEntries(); }, 120); });
    document.addEventListener("invalid", event => { if (event.target.closest("form")) markFieldError(event.target); }, true);
    document.addEventListener("input", event => { if (event.target.dataset.errorId && event.target.validity.valid) clearFieldError(event.target); });
    document.addEventListener("click", event => { if (event.target.closest('a[href^="/products/"]')) saveView(); });
    view.listen(window, "pagehide", saveView);

    document.addEventListener("visibilitychange", () => { clearTimeout(state.timer); if (!document.hidden && state.autoRefresh) refresh(); });
    loadView();
  }

  applyLanguage(); wire(); renderPage(); refresh();
  if (new URL(view.url).hash === "#environment") openEnvironment();
  setTimeout(() => { if (state.loading) renderEntries(); }, 300);
  state.projectionTimer = setInterval(refreshRuntimeProjection, 1000);
  return {
    pause() { saveView(); ++state.refreshToken; clearTimeout(state.timer); clearInterval(state.projectionTimer); },
    resume() { applyLanguage(); clearInterval(state.projectionTimer); state.projectionTimer = setInterval(refreshRuntimeProjection, 1000); if (state.autoRefresh) refresh(); },
    dispose() { clearTimeout(state.timer); clearInterval(state.projectionTimer); },
  };
});
