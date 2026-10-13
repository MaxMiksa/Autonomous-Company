const els = {
  pulseDot: document.getElementById("pulseDot"),
  pulseText: document.getElementById("pulseText"),
  lastUpdate: document.getElementById("lastUpdate"),
  latency: document.getElementById("latency"),

  guardianState: document.getElementById("guardianState"),
  guardianMeta: document.getElementById("guardianMeta"),
  daemonState: document.getElementById("daemonState"),
  daemonMeta: document.getElementById("daemonMeta"),
  loopState: document.getElementById("loopState"),
  loopMeta: document.getElementById("loopMeta"),
  autostartState: document.getElementById("autostartState"),
  autostartMeta: document.getElementById("autostartMeta"),
  graftState: document.getElementById("graftState"),
  graftMeta: document.getElementById("graftMeta"),

  cardGuardian: document.getElementById("cardGuardian"),
  cardDaemon: document.getElementById("cardDaemon"),
  cardLoop: document.getElementById("cardLoop"),
  cardAutostart: document.getElementById("cardAutostart"),
  cardGraft: document.getElementById("cardGraft"),

  stateList: document.getElementById("stateList"),
  consensusText: document.getElementById("consensusText"),
  ideasText: document.getElementById("ideasText"),
  ideasBadge: document.getElementById("ideasBadge"),
  analystText: document.getElementById("analystText"),
  analystBadge: document.getElementById("analystBadge"),
  analystCopy: document.getElementById("analystCopy"),
  analystCopyAll: document.getElementById("analystCopyAll"),
  analystRunNow: document.getElementById("analystRunNow"),
  analystRunStatus: document.getElementById("analystRunStatus"),
  logText: document.getElementById("logText"),
  rawText: document.getElementById("rawText"),

  creditBadge: document.getElementById("creditBadge"),
  costWindow: document.getElementById("costWindow"),
  costWindowLabel: document.getElementById("costWindowLabel"),
  costTotal: document.getElementById("costTotal"),
  costLast: document.getElementById("costLast"),
  costCycles: document.getElementById("costCycles"),
  costLimits: document.getElementById("costLimits"),
  costFallbacks: document.getElementById("costFallbacks"),
  costOffloads: document.getElementById("costOffloads"),
  costBudget: document.getElementById("costBudget"),
  costEngine: document.getElementById("costEngine"),
  codexWindow: document.getElementById("codexWindow"),
  ccusageBlock: document.getElementById("ccusageBlock"),
  costTotalLabel: document.getElementById("costTotalLabel"),
  costAllTotal: document.getElementById("costAllTotal"),
  costAllCycles: document.getElementById("costAllCycles"),
  costAllLimits: document.getElementById("costAllLimits"),
  ccusageRange: document.getElementById("ccusageRange"),
  ccTotal: document.getElementById("ccTotal"),
  ccTotalLabel: document.getElementById("ccTotalLabel"),
  ccClaude: document.getElementById("ccClaude"),
  ccCodex: document.getElementById("ccCodex"),
  ccModels: document.getElementById("ccModels"),

  directiveInput: document.getElementById("directiveInput"),
  directiveBadge: document.getElementById("directiveBadge"),
  directiveStatus: document.getElementById("directiveStatus"),
  directiveCurrent: document.getElementById("directiveCurrent"),
  directiveUpdated: document.getElementById("directiveUpdated"),
  directiveSummary: document.getElementById("directiveSummary"),
  directiveSections: document.getElementById("directiveSections"),
  btnDirective: document.getElementById("btnDirective"),
  settingsForm: document.getElementById("settingsForm"),
  settingsBadge: document.getElementById("settingsBadge"),
  settingsStatus: document.getElementById("settingsStatus"),
  btnSaveSettings: document.getElementById("btnSaveSettings"),
  btnRedeploy: document.getElementById("btnRedeploy"),
  btnWake: document.getElementById("btnWake"),

  btnRefresh: document.getElementById("btnRefresh"),
  btnHold: document.getElementById("btnHold"),
  btnRelease: document.getElementById("btnRelease"),
  holdBadge: document.getElementById("holdBadge"),
  btnTail: document.getElementById("btnTail"),
  btnRaw: document.getElementById("btnRaw"),
  btnConsensusFull: document.getElementById("btnConsensusFull"),
  consensusBadge: document.getElementById("consensusBadge"),
  autoToggle: document.getElementById("autoToggle"),
  refreshInterval: document.getElementById("refreshInterval"),
};

let timer = null;
let rawVisible = false;
let consensusFullShown = false;
let lastHold = null;
let lastDirective = null;

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderInlineMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return html;
}

function renderMarkdown(md) {
  const lines = String(md || "").replace(/\r\n?/g, "\n").split("\n");
  const out = [];
  let inList = false;
  let inCode = false;
  let inParagraph = false;

  const closeParagraph = () => {
    if (inParagraph) {
      out.push("</p>");
      inParagraph = false;
    }
  };
  const closeList = () => {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  };

  for (const line of lines) {
    if (line.startsWith("```")) {
      closeParagraph();
      closeList();
      if (!inCode) {
        out.push("<pre><code>");
        inCode = true;
      } else {
        out.push("</code></pre>");
        inCode = false;
      }
      continue;
    }

    if (inCode) {
      out.push(`${escapeHtml(line)}\n`);
      continue;
    }

    if (!line.trim()) {
      closeParagraph();
      closeList();
      continue;
    }

    const h = line.match(/^(#{1,6})\s+(.*)$/);
    if (h) {
      closeParagraph();
      closeList();
      const level = h[1].length;
      out.push(`<h${level}>${renderInlineMarkdown(h[2].trim())}</h${level}>`);
      continue;
    }

    const li = line.match(/^\s*[-*]\s+(.*)$/);
    if (li) {
      closeParagraph();
      if (!inList) {
        out.push("<ul>");
        inList = true;
      }
      out.push(`<li>${renderInlineMarkdown(li[1].trim())}</li>`);
      continue;
    }

    closeList();
    if (!inParagraph) {
      out.push("<p>");
      inParagraph = true;
    } else {
      out.push("<br />");
    }
    out.push(renderInlineMarkdown(line.trim()));
  }

  closeParagraph();
  closeList();
  if (inCode) {
    out.push("</code></pre>");
  }

  return out.join("");
}

function classForState(kind, state) {
  if (kind === "daemon") {
    if (state === "active") return "good";
    if (state === "inactive" || state === "not_installed" || state === "unsupported") return "warn";
    return "bad";
  }
  if (kind === "loop") {
    if (state === "running") return "good";
    if (state === "stopped") return "warn";
    return "bad";
  }
  if (kind === "guardian") {
    if (state === "running") return "good";
    if (state === "stopped" || state === "unsupported") return "warn";
    return "bad";
  }
  if (kind === "autostart") {
    if (state === "configured") return "good";
    if (state === "not_configured" || state === "unsupported") return "warn";
    return "bad";
  }
  return "warn";
}

function applyCardState(card, kind, state) {
  card.classList.remove("good", "warn", "bad");
  card.classList.add(classForState(kind, state));
}

function renderGraft(g) {
  g = g || {};
  els.cardGraft.classList.remove("good", "warn", "bad");
  if (g.available === false) {
    els.graftState.textContent = "yerel";
    els.graftMeta.textContent = "n/a (git yok)";
    return;
  }
  const behind = g.behind == null ? "?" : g.behind;
  const age = g.age_h == null ? "?" : Math.round(g.age_h);
  if (g.refreshing) {
    els.graftState.textContent = "TAZELENİYOR";
    els.graftMeta.textContent = `${behind}c/${age}s · --deep koşuyor`;
    els.cardGraft.classList.add("warn");
    return;
  }
  const stale =
    g.behind != null && g.max_behind != null && g.behind > g.max_behind &&
    g.age_h != null && g.max_age_h != null && g.age_h > g.max_age_h;
  els.graftState.textContent = stale ? "BAYAT" : "TAZE";
  els.graftMeta.textContent =
    `${behind}c/${age}s · eşik ${g.max_behind ?? "?"}c/${g.max_age_h ?? "?"}s`;
  els.cardGraft.classList.add(stale ? "warn" : "good");
}

function formatTime(isoText) {
  try {
    return new Date(isoText).toLocaleString();
  } catch {
    return isoText;
  }
}

function renderStateList(parsed, stateFile, router) {
  router = router || {};
  const routed = (router.routedEngine || "").toUpperCase();
  const routedModel = router.routedModel
    ? router.routedModel + (router.routedEffort ? ` · effort ${router.routedEffort}` : "")
    : "-";
  const ladder = (arr) => (Array.isArray(arr) && arr.length ? arr.join(" → ") : "-");
  const budgetInterval = (router.dailyBudget || router.weeklyBudget)
    ? `Daily $${router.dailyBudget || "-"} · Weekly $${router.weeklyBudget || "-"} · ${router.interval || "-"}s`
    : `$${router.windowBudget || "-"} cap · ${router.interval || "-"}s`;

  const rows = [
    ["Active engine (routed)", routed || "-"],
    ["Active model", routedModel],
    ["Router decision", router.routerReason || "-"],
    ["Tier selection", router.tierMode || "-"],
    ["Claude ladder (cheap→capable)", ladder(router.claudeLadder)],
    ["Codex effort ladder", ladder(router.codexLadder)],
    ["Base engine / model", `${parsed.loop.engine || "-"} / ${parsed.loop.model || "-"}`],
    ["Budget / interval", budgetInterval],
    ["Loop Count", parsed.loop.loopCount || stateFile.LOOP_COUNT || "-"],
    ["Error Count", parsed.loop.errorCount || stateFile.ERROR_COUNT || "-"],
    ["Last Run", parsed.loop.lastRun || stateFile.LAST_RUN || "-"],
    ["Daemon ActiveState", parsed.daemon.activeState || "-"],
  ];

  els.stateList.innerHTML = rows
    .map(([k, v]) => `<div><dt>${k}</dt><dd>${String(v)}</dd></div>`)
    .join("");
}

async function fetchStatus() {
  const started = performance.now();
  const res = await fetch("/api/status", { cache: "no-store" });
  const data = await res.json();
  const elapsed = Math.round(performance.now() - started);

  const parsed = data.parsed || {};
  const guardian = parsed.guardian || {};
  const daemon = parsed.daemon || {};
  const loop = parsed.loop || {};
  const autostart = parsed.autostart || {};

  els.guardianState.textContent = (guardian.state || "unknown").toUpperCase();
  els.guardianMeta.textContent = guardian.pid ? `PID ${guardian.pid}` : "PID --";
  applyCardState(els.cardGuardian, "guardian", guardian.state);

  els.daemonState.textContent = (daemon.state || "unknown").toUpperCase();
  els.daemonMeta.textContent = daemon.mainPid ? `MainPID ${daemon.mainPid}` : "MainPID --";
  applyCardState(els.cardDaemon, "daemon", daemon.state);

  els.loopState.textContent = (loop.state || "unknown").toUpperCase();
  const loopCycle = loop.loopCount ? `Cycle ${loop.loopCount}` : "Cycle --";
  const loopPid = loop.pid ? `PID ${loop.pid}` : "PID --";
  els.loopMeta.textContent = `${loopCycle} | ${loopPid}`;
  applyCardState(els.cardLoop, "loop", loop.state);

  els.autostartState.textContent = (autostart.state || "unknown").toUpperCase();
  els.autostartMeta.textContent = autostart.raw || "Autostart";
  applyCardState(els.cardAutostart, "autostart", autostart.state);

  renderStateList(parsed, data.stateFile || {}, data.router || {});
  setWakeAvailability(data.stateFile || {});

  // The status poll carries a 3000-char head. Do not overwrite the panel while the
  // operator is reading the full file — that made the view silently snap back.
  if (!consensusFullShown) {
    const consensusRaw = (data.consensusHead || parsed.consensusPreview || "(no consensus)").trim();
    els.consensusText.innerHTML = renderMarkdown(consensusRaw);
    const total = data.consensusBytes || 0;
    const shown = new TextEncoder().encode(consensusRaw).length;
    if (els.consensusBadge) {
      els.consensusBadge.textContent = total > shown
        ? "head · " + shown.toLocaleString() + " of " + total.toLocaleString() + " bytes"
        : "full · " + total.toLocaleString() + " bytes";
    }
  }
  els.logText.textContent = (data.logTail || parsed.recentLog || "(no logs yet)").trim();
  els.rawText.textContent = data.raw || "";

  const healthy = data.ok && loop.state === "running" && daemon.state === "active";
  els.pulseText.textContent = healthy ? "Live Link: STABLE" : "Live Link: ATTENTION";
  els.pulseDot.style.background = healthy ? "var(--good)" : "var(--warn)";

  renderDirective(data.directive || {});
  renderCost(data.cost || {});
  lastHold = data.hold || { held: false };
  renderHold(lastHold);
  renderGraft(data.graft || {});

  els.lastUpdate.textContent = `Last update: ${formatTime(data.timestamp)}`;
  els.latency.textContent = `Roundtrip: ${elapsed}ms`;
}

function renderCost(cost) {
  const usd = (n) => `$${(Number(n) || 0).toFixed(2)}`;
  if (cost.gateDailyCap) {
    els.costWindow.textContent = usd(cost.gateDailyUsd);
    els.costWindowLabel.textContent = `Bugün / $${cost.gateDailyCap} cap (gate)`;
  } else {
    els.costWindow.textContent = usd(cost.windowUsd);
    els.costWindowLabel.textContent = cost.windowBudget
      ? `5h window / $${cost.windowBudget} cap`
      : "5h window";
  }
  // Haftalık pencere (Pzt 00:00 UTC'de sıfırlanır) — manşet değerler; all-time alt satırda.
  els.costTotal.textContent = usd(cost.weekUsd ?? cost.totalUsd);
  if (els.costTotalLabel) {
    els.costTotalLabel.textContent = cost.weekStart ? `Bu hafta (${cost.weekStart} →)` : "Bu hafta";
  }
  els.costLast.textContent = usd(cost.lastUsd);
  els.costCycles.textContent = cost.weekCycles ?? cost.cycles ?? 0;
  els.costLimits.textContent = cost.weekLimitHits ?? 0;
  els.costFallbacks.textContent = cost.weekFallbacks ?? 0;
  els.costOffloads.textContent = cost.weekOffloads ?? 0;
  els.costBudget.textContent = cost.weekGatePauses ?? 0;
  if (els.costAllTotal) els.costAllTotal.textContent = usd(cost.totalUsd);
  if (els.costAllCycles) els.costAllCycles.textContent = cost.cycles ?? 0;
  if (els.costAllLimits) els.costAllLimits.textContent = cost.limitHits ?? 0;
  els.costEngine.textContent = (cost.engine || "—").toUpperCase();
  els.codexWindow.textContent = cost.codexWindow ?? 0;

  renderCcusage(cost.ccusage || {});

  const reason = (cost.creditReason || "").trim();
  if (reason === "out_of_credits") {
    // Pay-as-you-go OVERFLOW credits are off — expected under the cost cap. The
    // company runs on the Max subscription window, so this is informational, not
    // a failure. Health is whether cycles keep completing (see Loop/Cost above).
    els.creditBadge.textContent = "SUBSCRIPTION ONLY";
    els.creditBadge.className = "badge badge-none";
    els.creditBadge.title =
      "No pay-as-you-go extra credits (overflow off — intended). Cycles run on the Max plan window.";
  } else if (reason) {
    els.creditBadge.textContent = reason.toUpperCase();
    els.creditBadge.className = "badge badge-pending";
    els.creditBadge.title = "";
  } else {
    els.creditBadge.textContent = "OK";
    els.creditBadge.className = "badge badge-done";
    els.creditBadge.title = "";
  }
}

function renderCcusage(cc) {
  if (!els.ccusageBlock) return;
  const usd = (n) => `$${(Number(n) || 0).toFixed(2)}`;
  if (!cc.available) {
    // Fail open: hide the block when ccusage isn't installed / still computing.
    els.ccusageBlock.hidden = true;
    return;
  }
  els.ccusageBlock.hidden = false;
  els.ccTotal.textContent = usd(cc.totalCost);
  els.ccTotalLabel.textContent = cc.days ? `Hafta (${cc.days}g)` : "Hafta";
  els.ccClaude.textContent = usd(cc.claudeCost);
  els.ccCodex.textContent = usd(cc.codexCost);
  els.ccusageRange.textContent = cc.today && cc.today.date
    ? `${cc.today.date} · ${usd(cc.today.cost)}`
    : "";
  const models = Array.isArray(cc.models) ? cc.models : [];
  els.ccModels.textContent = models.length
    ? models.map((m) => `${m.name} ${usd(m.cost)}`).join(" · ")
    : "—";
}

// Start/Stop used to live here and were permanently disabled in the container (the
// loop is a child of the entrypoint, managed by Coolify — both were no-ops). They are
// replaced by Hold/Release, which drive logs/LOOP_HOLD: the only control that actually
// stops the loop, and the one the operator was reaching for anyway.
function renderHold(hold) {
  if (!els.holdBadge) return;
  const held = !!(hold && hold.held);
  els.holdBadge.textContent = held
    ? (hold.kind === "operator" ? "HELD (operator)" : "HELD (budget/loop latch)")
    : "running";
  els.holdBadge.className = "badge " + (held ? "badge-pending" : "badge-none");
  els.holdBadge.title = held ? `${hold.reason || ""}${hold.latched ? " · latched " + hold.latched : ""}` : "";
  els.btnHold.disabled = held;
  els.btnRelease.disabled = !held;
}

async function setHold(arm) {
  const btn = arm ? els.btnHold : els.btnRelease;
  const hold = lastHold || {};
  if (arm) {
    const reason = prompt("Hold reason (recorded in logs/hold-audit.log):", "operator pause");
    if (reason === null) return;                       // cancelled
    var body = JSON.stringify({ reason });
  } else if (hold.kind && hold.kind !== "operator") {
    // Releasing a latch the LOOP wrote is not the same act as undoing your own pause:
    // the file's own text says to clear it only after verifying the accounting.
    if (!confirm(`This hold was NOT set from the cockpit:\n\n${hold.reason || "(no reason recorded)"}\n\nReleasing it overrides whatever latched it. Continue?`)) return;
  }
  const label = btn.textContent;
  btn.disabled = true;
  btn.textContent = `${label}...`;
  try {
    const res = await fetch(arm ? "/api/hold" : "/api/hold/release", {
      method: "POST",
      headers: arm ? { "Content-Type": "application/json" } : {},
      body: arm ? body : undefined,
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "hold change failed");
    await fetchStatus();
  } catch (err) {
    alert(err instanceof Error ? err.message : String(err));
  } finally {
    btn.textContent = label;
    fetchStatus().catch(() => {});
  }
}

function renderDirective(directive) {
  lastDirective = directive || null;
  const status = (directive.status || "NONE").toUpperCase();
  els.directiveBadge.textContent = status;
  els.directiveBadge.className = `badge badge-${status.toLowerCase()}`;

  if (directive.present && directive.directive) {
    els.directiveCurrent.textContent = directive.directive;
    els.directiveUpdated.textContent = directive.updated
      ? `updated ${formatTime(directive.updated)}`
      : "";
  } else {
    els.directiveCurrent.textContent = "(none)";
    els.directiveUpdated.textContent = "";
  }
  renderDirectiveSections(directive);
}

// One-line section summary + per-section list (2026-10-13). The body is now built by
// append/archive, so its shape (how many live sections, how many archive summaries,
// how big) is what the operator needs to see before reading 40 KB of text.
function renderDirectiveSections(directive) {
  const secs = (directive && directive.present && Array.isArray(directive.sections))
    ? directive.sections : [];
  els.directiveSummary.textContent = "";
  els.directiveSummary.classList.remove("directive-summary-warn");
  els.directiveSections.replaceChildren();
  if (!secs.length) return;
  const kb = (b) => `${(b / 1024).toFixed(1)} KB`;
  const active = secs.filter((s) => s.kind === "active");
  const archived = secs.filter((s) => s.kind === "archive");
  const last = active.length ? active[active.length - 1].heading : "";
  const lastShort = last.length > 60 ? `${last.slice(0, 59)}…` : last;
  const parts = [
    `${secs.length} sections`,
    kb(directive.bodyBytes || 0),
    `active ${active.length}`,
    `archive ${archived.length}`,
  ];
  if (lastShort) parts.push(`last: ${lastShort}`);
  els.directiveSummary.textContent = parts.join(" · ");
  if ((directive.bodyBytes || 0) > (directive.warnBytes || 50000)) {
    els.directiveSummary.classList.add("directive-summary-warn");
    els.directiveSummary.title = "Body is over the writer's warning size — archive closed sections.";
  } else {
    els.directiveSummary.title = "";
  }
  for (const s of secs) {
    const li = document.createElement("li");
    const badge = document.createElement("span");
    badge.className = `badge badge-sec-${s.kind}`;
    badge.textContent = s.kind;
    const size = document.createElement("span");
    size.className = "muted mono";
    size.textContent = kb(s.bytes || 0);
    const title = document.createElement("span");
    title.textContent = s.heading;
    li.append(badge, " ", size, " ", title);
    els.directiveSections.appendChild(li);
  }
}

async function submitDirective() {
  const text = els.directiveInput.value.trim();
  if (!text) {
    els.directiveStatus.textContent = "Type a directive first.";
    return;
  }
  const label = els.btnDirective.textContent;
  els.btnDirective.disabled = true;
  els.btnDirective.textContent = "Sending...";
  els.directiveStatus.textContent = "";
  try {
    const send = (allowPending) => fetch("/api/directive", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(allowPending ? { directive: text, allowPending: true }
                                        : { directive: text }),
    });
    let res = await send(false);
    let data = await res.json();
    // The writer REFUSES to overwrite a live PENDING directive — that gate is the
    // point, not an error. The server has always accepted `allowPending` for the
    // deliberate supersede; the panel just never offered it, so a refusal was a
    // dead end here and the operator had to fall back to the CLI. Ask, then retry.
    if ((!res.ok || !data.ok) && data.needsAllowPending) {
      const cur = (lastDirective && lastDirective.updated) ? ` (last updated ${lastDirective.updated})` : "";
      if (confirm(`The live directive is still PENDING${cur} — work is in flight.\n\n${data.error}\n\nAdd the text in the box as one more section anyway? Nothing already there is deleted.`)) {
        res = await send(true);
        data = await res.json();
      }
    }
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Failed to send directive");
    }
    els.directiveInput.value = "";
    els.directiveStatus.textContent = "Section added — Status is PENDING, the next cycle will pick it up.";
    renderDirective(data.directive || {});
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    els.directiveStatus.textContent = msg;
  } finally {
    els.btnDirective.disabled = false;
    els.btnDirective.textContent = label;
  }
}

function renderSettings(settings) {
  const spec = settings.spec || [];
  const values = settings.values || {};
  els.settingsForm.innerHTML = "";
  for (const s of spec) {
    const row = document.createElement("label");
    row.className = "settings-row";
    const cur = values[s.key] ?? "";
    const labelHtml = `<span class="settings-label">${s.label}<code>${s.key}</code></span>`;
    if (s.type === "bool") {
      row.innerHTML = `${labelHtml}<input type="checkbox" data-key="${s.key}" ${
        cur === "1" ? "checked" : ""
      } />`;
    } else {
      row.innerHTML = `${labelHtml}<input type="${
        s.type === "number" ? "text" : "text"
      }" data-key="${s.key}" value="${String(cur).replace(/"/g, "&quot;")}" placeholder="(default)" />`;
    }
    els.settingsForm.appendChild(row);
  }
}

function gatherSettings() {
  const out = {};
  els.settingsForm.querySelectorAll("[data-key]").forEach((el) => {
    const key = el.getAttribute("data-key");
    out[key] = el.type === "checkbox" ? (el.checked ? "1" : "0") : el.value.trim();
  });
  return out;
}

let ideasLoaded = false;
async function loadIdeas() {
  try {
    const res = await fetch("/api/ideas", { cache: "no-store" });
    const data = await res.json();
    ideasLoaded = true;
    if (data && data.present) {
      els.ideasText.innerHTML = renderMarkdown(data.markdown || "");
      // The file's own H1 carries a rewrite stamp (e.g. "rewritten Cycle 106,
      // 2026-07-24") that reads like staleness; the mtime is the real freshness.
      els.ideasBadge.textContent = data.updated
        ? "LOADED · file updated " + formatTime(data.updated)
        : "LOADED";
      els.ideasBadge.classList.remove("badge-none");
    } else {
      els.ideasText.textContent = "(no opportunity-scan.md yet)";
    }
  } catch (err) {
    ideasLoaded = false;
    els.ideasText.textContent = "Failed to load ideas — will retry when you close and reopen this panel.";
  }
}

let toolUsageLoaded = false;
async function loadToolUsage() {
  const text = document.getElementById("toolUsageText");
  const badge = document.getElementById("toolUsageBadge");
  try {
    const res = await fetch("/api/tool-usage", { cache: "no-store" });
    const data = await res.json();
    toolUsageLoaded = true;
    if (data && data.present) {
      // Real table, not padded text: the cockpit's .mono class is Rajdhani (proportional),
      // so character-count alignment can never line up. Values are our own ledger's
      // numbers/ISO dates; render as numbers to keep the cells inert.
      // brw = all browser work (harness + raw MCP + site-contact-evidence); mcp = raw
      // mcp__browseros__ micro-steps only. The harness is meant to move work from mcp into
      // brw, so showing both is what makes the change legible instead of a mystery drop.
      const cols = ["ctx7", "airtable_r", "airtable_w", "linear", "browser", "browser_mcp", "graft", "calls", "cycles"];
      const heads = ["date", "ctx7", "air-r", "air-w", "linear", "brw", "brw-mcp", "graft", "calls", "cycles"];
      let html = "<table class=\"usage-table\"><thead><tr>" +
        heads.map((h) => `<th>${h}</th>`).join("") + "</tr></thead><tbody>";
      for (const d of data.days) {
        html += "<tr><td>" + String(d.date).slice(0, 10) + "</td>" +
          cols.map((k) => `<td>${Number(d[k]) || 0}</td>`).join("") + "</tr>";
      }
      html += "</tbody></table>";
      text.innerHTML = html;
      badge.textContent = data.updated ? "LOADED · " + formatTime(data.updated) : "LOADED";
      badge.classList.remove("badge-none");
    } else {
      text.textContent =
        "(no ledger yet — tool-usage-audit.py starts writing at the loop's next restart; " +
        "it backfills retained cycles on its first run)";
    }
  } catch (err) {
    toolUsageLoaded = false;
    text.textContent = "Failed to load tool usage — will retry when you close and reopen this panel.";
  }
}

let analystLoaded = false;
let analystRaw = "";
async function loadAnalysis() {
  try {
    const res = await fetch("/api/analysis", { cache: "no-store" });
    const data = await res.json();
    // Only latch the loaded flag on SUCCESS: it used to be set at the call
    // site before the fetch resolved, so one transient failure (e.g. the panel
    // expanded during a container swap) stuck as "Failed to load analysis."
    // until a full page reload, even though the backend was healthy.
    analystLoaded = true;
    if (data && data.present) {
      analystRaw = data.markdown || "";
      els.analystText.innerHTML = renderMarkdown(analystRaw);
      els.analystBadge.textContent = data.updated
        ? "LOADED · file updated " + formatTime(data.updated)
        : "LOADED";
      els.analystBadge.classList.remove("badge-none");
    } else {
      els.analystText.textContent = "(no analysis yet — the Codex analyst cron has not run)";
    }
    renderAnalystTrigger(data && data.trigger);
  } catch (err) {
    analystLoaded = false;
    els.analystText.textContent = "Failed to load analysis — will retry when you close and reopen this panel.";
  }
}

// On-demand run lifecycle, from the host watcher's volume markers. The button is a
// courtesy — the server refuses doubles, the host flock is the real guard.
function renderAnalystTrigger(trigger) {
  if (!els.analystRunStatus) return;
  if (!trigger) { els.analystRunStatus.textContent = ""; return; }
  if (trigger.running) {
    els.analystRunStatus.textContent = `Analyst run IN FLIGHT (${trigger.running_info || "no info"})`;
    els.analystRunNow.disabled = true;
  } else if (trigger.pending) {
    els.analystRunStatus.textContent = "Run request QUEUED — the host watcher fires within 5 minutes.";
    els.analystRunNow.disabled = true;
  } else {
    els.analystRunStatus.textContent = trigger.last ? `Last on-demand run: ${trigger.last}` : "";
    els.analystRunNow.disabled = false;
  }
}

async function runAnalystNow() {
  if (!window.confirm("Queue an Opportunity Analyst run now? Starts within 5 minutes, takes ~15 minutes, costs ~$23.")) return;
  const label = els.analystRunNow.textContent;
  els.analystRunNow.disabled = true;
  els.analystRunNow.textContent = "Queuing...";
  try {
    const res = await fetch("/api/analyst/run", { method: "POST" });
    const data = await res.json();
    els.analystRunStatus.textContent = data.ok
      ? data.message
      : `Refused: ${data.error || "unknown reason"}`;
  } catch (err) {
    els.analystRunStatus.textContent = err instanceof Error ? err.message : String(err);
  } finally {
    els.analystRunNow.textContent = label;
    loadAnalysis().catch(() => {});
  }
}

// Extract just the paste-ready directive from the analyst report: the last fenced
// ```md / ```markdown block that looks like a directive; strip a leading
// "# Human Directive" line (the Director panel re-wraps it). Falls back to the
// "Paste-ready" section, then the whole report.
function extractDirective(md) {
  if (!md) return "";
  const fences = [...md.matchAll(/```(?:md|markdown)?\s*\n([\s\S]*?)```/g)];
  for (let i = fences.length - 1; i >= 0; i--) {
    const b = fences[i][1];
    if (/human directive|##\s*decision|##\s*authorization|##\s*directive|status:/i.test(b)) {
      return b.replace(/^\s*#\s*Human Directive\s*\n/i, "").trim();
    }
  }
  const m = md.match(/##\s*10\.[\s\S]*/);
  if (m) return m[0].trim();
  return md.trim();
}

async function copyToBtn(btn, text) {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    const prev = btn.textContent;
    btn.textContent = "Copied";
    setTimeout(() => { btn.textContent = prev; }, 1500);
  } catch (e) {}
}

if (els.analystCopy) {
  els.analystCopy.addEventListener("click", () => copyToBtn(els.analystCopy, extractDirective(analystRaw)));
}
if (els.analystCopyAll) {
  els.analystCopyAll.addEventListener("click", () => copyToBtn(els.analystCopyAll, analystRaw));
}
if (els.analystRunNow) {
  els.analystRunNow.addEventListener("click", runAnalystNow);
}

// Director panel: copy-to-clipboard directive templates (served from
// dashboard/directive-templates/*.md). Copy → paste into the box above → Send.
async function loadDirectiveTemplates() {
  const holder = document.getElementById("directiveTemplates");
  if (!holder) return;
  try {
    const res = await fetch("/api/directive-templates");
    const data = await res.json();
    const tpls = (data && data.templates) || [];
    holder.innerHTML = "";
    if (!tpls.length) {
      holder.innerHTML = '<span class="muted mono">(no templates)</span>';
      return;
    }
    tpls.forEach((t) => {
      const b = document.createElement("button");
      b.className = "tpl-btn";
      b.textContent = t.label;
      if (t.hint) b.title = t.hint;
      // Load it straight into the box (and keep the clipboard copy as a bonus).
      // These templates are fill-free by design, so the paste step was pure friction.
      b.addEventListener("click", () => {
        if (els.directiveInput) {
          els.directiveInput.value = t.text;
          els.directiveInput.focus();
          els.directiveInput.scrollTop = 0;
        }
        copyToBtn(b, t.text);
      });
      holder.appendChild(b);
    });
  } catch (e) {
    holder.innerHTML = '<span class="muted mono">(templates unavailable)</span>';
  }
}
loadDirectiveTemplates();

async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    renderSettings(data);
  } catch (err) {
    els.settingsForm.innerHTML = `<p class="muted">Failed to load settings.</p>`;
  }
}

async function saveSettings(withRedeploy) {
  els.btnSaveSettings.disabled = true;
  els.btnRedeploy.disabled = true;
  els.settingsStatus.textContent = "Saving...";
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values: gatherSettings() }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Save failed");
    renderSettings(data.settings || {});
    els.settingsStatus.textContent = "Saved. Applies after redeploy/restart.";
    if (withRedeploy) {
      els.settingsStatus.textContent = "Saved. Triggering redeploy...";
      const rd = await fetch("/api/redeploy", { method: "POST" });
      const rdData = await rd.json();
      els.settingsStatus.textContent =
        rd.ok && rdData.ok
          ? "Redeploy triggered — new config applies once it lands."
          : `Saved, but redeploy: ${rdData.error || "failed"}`;
    }
  } catch (err) {
    els.settingsStatus.textContent = err instanceof Error ? err.message : String(err);
  } finally {
    els.btnSaveSettings.disabled = false;
    els.btnRedeploy.disabled = false;
  }
}

// "Run cycle now" ends the sleep between cycles. It is enabled ONLY while the loop
// is idle: during a running cycle there is nothing to wake, and the only sleep alive
// then is the cycle-timeout watchdog, which must not be touched. The server enforces
// this too — the button state is a courtesy, not the guard.
function setWakeAvailability(stateFile) {
  const status = String((stateFile && stateFile.STATUS) || "").toLowerCase();
  const sleeping = status === "idle";
  els.btnWake.disabled = !sleeping;
  els.btnWake.title = sleeping
    ? "Loop is sleeping — start the next cycle now."
    : `Loop is ${status || "in an unknown state"} — nothing to wake.`;
}

async function wakeLoop() {
  const label = els.btnWake.textContent;
  els.btnWake.disabled = true;
  els.btnWake.textContent = "Waking...";
  try {
    const res = await fetch("/api/wake", { method: "POST" });
    const data = await res.json();
    els.settingsStatus.textContent =
      res.ok && data.ok
        ? "Cycle starting now — the wait was ended, LOOP_INTERVAL is unchanged."
        : `Wake refused: ${data.error || "unknown reason"}`;
  } catch (err) {
    els.settingsStatus.textContent = err instanceof Error ? err.message : String(err);
  } finally {
    els.btnWake.textContent = label;
    fetchStatus().catch(() => {});
  }
}


function resetAutoTimer() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
  if (els.autoToggle.checked) {
    timer = setInterval(() => {
      fetchStatus().catch(() => {});
      // Requests were fetched once at first paint only, so one filed mid-session stayed
      // invisible (and un-notified) until a manual reload. Same cadence as the status poll.
      loadOperatorRequests().catch(() => {});
    }, Number(els.refreshInterval.value));
  }
}

els.btnRefresh.addEventListener("click", () => fetchStatus().catch(() => {}));
els.btnHold.addEventListener("click", () => setHold(true));
els.btnRelease.addEventListener("click", () => setHold(false));
els.btnWake.addEventListener("click", () => wakeLoop());
els.btnTail.addEventListener("click", () => fetchStatus().catch(() => {}));
els.btnConsensusFull.addEventListener("click", async () => {
  if (consensusFullShown) {                    // collapse: let the next poll restore the head
    consensusFullShown = false;
    els.btnConsensusFull.textContent = "Show full file";
    fetchStatus().catch(() => {});
    return;
  }
  els.btnConsensusFull.textContent = "Loading...";
  try {
    const res = await fetch("/api/consensus");
    const data = await res.json();
    els.consensusText.innerHTML = renderMarkdown((data.text || "").trim());
    if (els.consensusBadge) {
      els.consensusBadge.textContent = "full · " + (data.bytes || 0).toLocaleString() + " bytes";
    }
    consensusFullShown = true;                 // set AFTER the render, so a poll landing
    els.btnConsensusFull.textContent = "Show head only";  // mid-fetch cannot leave it stuck
  } catch (err) {
    els.btnConsensusFull.textContent = "Show full file";
    els.consensusText.innerHTML = renderMarkdown("(could not load full consensus: " + err + ")");
  }
});
els.btnRaw.addEventListener("click", () => {
  rawVisible = !rawVisible;
  els.rawText.classList.toggle("hidden", !rawVisible);
});
els.btnDirective.addEventListener("click", () => submitDirective());
els.btnSaveSettings.addEventListener("click", () => saveSettings(false));
els.btnRedeploy.addEventListener("click", () => saveSettings(true));

// Collapsible panels (Settings, Current directive) — default collapsed via markup.
document.querySelectorAll(".collapse-toggle").forEach((btn) => {
  btn.addEventListener("click", () => {
    const target = document.getElementById(btn.getAttribute("data-target"));
    if (!target) return;
    const collapsed = target.classList.toggle("collapsed");
    btn.setAttribute("aria-expanded", String(!collapsed));
    if (btn.getAttribute("data-target") === "ideasBody" && !collapsed && !ideasLoaded) {
      loadIdeas().catch(() => {});
    }
    if (btn.getAttribute("data-target") === "toolUsageBody" && !collapsed && !toolUsageLoaded) {
      loadToolUsage();
    }
    if (btn.getAttribute("data-target") === "analystBody" && !collapsed && !analystLoaded) {
      loadAnalysis().catch(() => {});
    }
  });
});
// --- Requests to you (operator requests) -------------------------------------------
// Answers go to memories/operator-decisions.md, NOT to the directive slot, so replying
// here can never overwrite a directive the loop is mid-way through executing.
const AUTH_LABELS = ["System", "Action", "Target", "Limit"];
const opreqEls = {
  list: document.getElementById("opreqList"),
  badge: document.getElementById("opreqBadge"),
  notify: document.getElementById("btnNotify"),
};

// Desktop notification for a newly filed request (2026-08-06). The panel already
// showed a badge, but nothing polled the endpoint after first paint, so a request
// filed mid-session stayed invisible until a manual reload — the badge was honest
// and useless at the same time. loadOperatorRequests() now runs on the poll timer,
// and any request ID we have not announced before raises one notification.
//
// Scope, stated plainly: this only fires while the cockpit tab is open (no service
// worker, no push subscription). Telegram remains the away-from-desk channel; this
// is for the case where the cockpit is up on a second screen.
const NOTIFIED_KEY = "opreqNotifiedIds";

function notifiedIds() {
  try {
    const raw = localStorage.getItem(NOTIFIED_KEY);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

function rememberNotified(ids) {
  try {
    // Keep the last 200 so the key cannot grow without bound over months.
    localStorage.setItem(NOTIFIED_KEY, JSON.stringify([...ids].slice(-200)));
  } catch {
    /* private mode / storage disabled — notifications simply repeat, never throw */
  }
}

function renderNotifyButton() {
  if (!opreqEls.notify) return;
  const supported = "Notification" in window;
  if (!supported) {
    opreqEls.notify.textContent = "Notifications n/a";
    opreqEls.notify.disabled = true;
    opreqEls.notify.title = "This browser exposes no Notification API";
    return;
  }
  const perm = Notification.permission;
  opreqEls.notify.textContent =
    perm === "granted" ? "Notifying" : perm === "denied" ? "Notifications blocked" : "Notify me";
  opreqEls.notify.disabled = perm !== "default";
  if (perm === "denied") {
    opreqEls.notify.title = "Blocked in browser settings — re-allow it there, this page cannot ask again";
  } else if (perm === "granted") {
    opreqEls.notify.title = "You get a desktop notification for each new request, while this tab is open";
  }
}

function announceNewRequests(open) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const seen = notifiedIds();
  const fresh = open.filter((r) => r && r.id && !seen.has(r.id));
  if (!fresh.length) return;

  fresh.forEach((req) => {
    const n = new Notification(`Auto-Company: ${req.id}`, {
      body: (req.requiredInput || "A decision is waiting on you.").slice(0, 180),
      tag: req.id, // same request never stacks duplicates
      requireInteraction: true, // a decision request should not vanish after 5 seconds
    });
    n.onclick = () => {
      window.focus();
      document.querySelector(".panel.opreq")?.scrollIntoView({ behavior: "smooth" });
      n.close();
    };
    seen.add(req.id);
  });
  rememberNotified(seen);
}

// Never redraw a card the operator is mid-answer in. The poll added on 2026-08-06 made
// this panel refresh on a timer, and the first real use of it lost a long refusal the
// operator had typed: the poll landed, innerHTML was rebuilt, the textarea went empty.
// Any focus inside the panel, or any field with content in it, defers the redraw — the
// badge and the notification still update, only the DOM the operator is typing into is
// left alone.
function opreqPanelBusy() {
  const panel = document.querySelector(".panel.opreq");
  if (!panel) return false;
  if (panel.contains(document.activeElement)) return true;
  return [...panel.querySelectorAll("textarea, input")].some(
    (el) => typeof el.value === "string" && el.value.trim() !== ""
  );
}

function renderOperatorRequests(payload) {
  const open = (payload && payload.open) || [];
  opreqEls.badge.textContent = String(open.length);
  opreqEls.badge.className = `badge badge-${open.length ? "pending" : "none"}`;
  announceNewRequests(open);

  if (opreqPanelBusy()) return;

  if (!open.length) {
    opreqEls.list.innerHTML = '<p class="muted mono">Nothing waiting on you.</p>';
    return;
  }

  opreqEls.list.innerHTML = open
    .map((req) => {
      const fields = req.authorizable
        ? AUTH_LABELS.map(
            (label) => `
          <label class="opreq-field">
            <span class="opreq-field-label">${label}</span>
            <textarea rows="2" data-field="${label}">${escapeHtml(
              (req.proposed && req.proposed[label]) || ""
            )}</textarea>
          </label>`
          ).join("")
        : `<p class="muted">This request type is not answered with an authorization block.
             Refuse it here, or answer it in a directive.</p>`;
      const authBtn = req.authorizable
        ? `<button class="btn btn-start" data-act="authorize">Authorize</button>`
        : "";
      return `
      <article class="opreq-card" data-id="${escapeHtml(req.id)}">
        <div class="opreq-head">
          <span class="mono opreq-id">${escapeHtml(req.id)}</span>
          <span class="muted mono">${escapeHtml(req.type)} · blocks ${escapeHtml(
        req.blockedScope || "—"
      )}</span>
        </div>
        <p class="opreq-question">${escapeHtml(req.requiredInput)}</p>
        <details class="opreq-form" ${req.authorizable ? "" : "open"}>
          <summary>Proposed authorization — read and edit before approving</summary>
          ${fields}
        </details>
        <label class="opreq-field">
          <span class="opreq-field-label">Reason (refusal only)</span>
          <textarea rows="1" data-reason="1" placeholder="why you are declining"></textarea>
        </label>
        <div class="director-actions">
          ${authBtn}
          <button class="btn btn-stop" data-act="refuse">Refuse</button>
          <span class="muted mono" data-status="1"></span>
        </div>
      </article>`;
    })
    .join("");

  opreqEls.list.querySelectorAll("button[data-act]").forEach((btn) => {
    btn.addEventListener("click", () => submitDecision(btn));
  });
}

async function submitDecision(btn) {
  const card = btn.closest(".opreq-card");
  const statusEl = card.querySelector("[data-status]");
  const decision = btn.getAttribute("data-act");
  const fields = {};
  AUTH_LABELS.forEach((label) => {
    const box = card.querySelector(`[data-field="${label}"]`);
    fields[label] = box ? box.value : "";
  });
  const reasonBox = card.querySelector("[data-reason]");

  card.querySelectorAll("button").forEach((b) => (b.disabled = true));
  statusEl.textContent = "Recording…";
  try {
    const res = await fetch("/api/operator-decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: card.getAttribute("data-id"),
        decision,
        fields,
        reason: reasonBox ? reasonBox.value : "",
      }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Failed to record decision");
    // Deliberately NOT a full re-render. The request legitimately stays OPEN until the
    // company's own verifier moves it, so redrawing the list would replace this card
    // with an identical one and silently erase the confirmation — the operator would
    // reasonably click again and append a duplicate decision.
    card.classList.add("opreq-answered");
    statusEl.textContent =
      decision === "authorize"
        ? "Authorized — recorded. The company applies it on its next cycle."
        : "Refused — recorded. The company will take no action on this.";
  } catch (err) {
    statusEl.textContent = err instanceof Error ? err.message : String(err);
    card.querySelectorAll("button").forEach((b) => (b.disabled = false));
  }
}

async function loadOperatorRequests() {
  try {
    const res = await fetch("/api/operator-requests");
    renderOperatorRequests(await res.json());
  } catch {
    opreqEls.list.innerHTML = '<p class="muted mono">(requests unavailable)</p>';
  }
}

els.autoToggle.addEventListener("change", resetAutoTimer);
els.refreshInterval.addEventListener("change", resetAutoTimer);

// Permission must be requested from a user gesture — asking on page load is what gets
// a site permanently blocked in Chrome. The first grant also announces whatever is
// already open, so pressing the button never leaves a pending request unannounced.
opreqEls.notify?.addEventListener("click", async () => {
  if (!("Notification" in window)) return;
  try {
    await Notification.requestPermission();
  } catch {
    /* older browsers use the callback form; renderNotifyButton reflects reality either way */
  }
  renderNotifyButton();
  loadOperatorRequests().catch(() => {});
});
renderNotifyButton();

loadOperatorRequests().catch(() => {});

fetchStatus().catch((err) => {
  const msg = err instanceof Error ? err.message : String(err);
  els.rawText.textContent = msg;
});
loadSettings().catch(() => {});
resetAutoTimer();
