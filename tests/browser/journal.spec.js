import { test as base, expect } from "@playwright/test";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import { createInterface } from "node:readline";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repository = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const envelope = data => ({ schemaVersion: 1, revision: 1, centerId: 'fixture', observedAt: new Date().toISOString(), data: { ...data, total: data.cycles.length, nextBefore: null } });
const python = process.env.AUTONOMOUS_COMPANY_BROWSER_PYTHON || process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");

async function refreshRecords(page) {
  await page.locator("#settingsButton").click();
  await page.locator("#refreshButton").click();
  await page.locator("#closeSettingsButton").click();
}

async function centerWrite(page, journal, route, data) {
  const response = await page.request.post(`${journal.url}/api/center/v1${route}`, { data, headers: { Origin: journal.url } });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()).data;
}

async function setLanguage(page, journal, language) {
  const prefs = (await (await page.request.get(`${journal.url}/api/center/v1/preferences`)).json()).data;
  await centerWrite(page, journal, '/preferences', { expectedRevision: prefs.revision,
    idempotencyKey: `language-${language}-${prefs.revision}`, preferences: { language } });
}

async function reimportProduct(page, journal, excludedEntry = null) {
  const candidate = await centerWrite(page, journal, '/imports/probe', { root: journal.directory });
  const result = await centerWrite(page, journal, '/imports/commit', { candidateId: candidate.candidateId,
    candidateHash: candidate.candidateHash, idempotencyKey: candidate.candidateId });
  for (const item of result.items) {
    const entry = (await (await page.request.get(`${journal.url}/api/center/v1/entries/${item.entryId}`)).json()).data;
    if (entry.kind === 'product' && entry.entryId !== excludedEntry) { Object.assign(journal, item); return; }
  }
  throw new Error('Fixture registration did not produce a product');
}

async function changeIdentityFixture(directory, code) {
  return promisify(execFile)(python, ["-c", [
    "import json, sys", "from pathlib import Path",
    "sys.path.insert(0, str(Path(sys.argv[1]) / 'scripts/core'))",
    "import product_identity as products", "root = Path(sys.argv[2])", code,
  ].join("\n"), repository, directory], { windowsHide: true });
}

const test = base.extend({
  journal: async ({}, use) => {
    const directory = await fs.mkdtemp(path.join(os.tmpdir(), "company-journal-browser-"));
    await fs.mkdir(path.join(directory, "logs"));
    await fs.mkdir(path.join(directory, "memories"));
    const start = Date.now() - 30 * 60 * 1000;
    const cycles = [1, 2, 3].map((number) => ({
      schema_version: 1, kind: "cycle_usage", project: "projects/journal-fixture", cycle_id: `cycle-000${number}-fixture`,
      cycle_number: number, engine: "codex", model: "gpt-6-astra",
      started_at: new Date(start + number * 60000).toISOString(),
      ended_at: new Date(start + number * 60000 + 30000).toISOString(),
      status: "completed", exit_code: 0,
      usage: { input_tokens: number === 2 ? null : 80, output_tokens: number === 2 ? null : 20,
        total_tokens: number === 2 ? null : 100, status: number === 2 ? "unavailable" : "reported" },
      cost_usd: null, cost_usd_status: "unavailable",
    }));
    await fs.writeFile(path.join(directory, "logs", "usage.jsonl"), cycles.map(JSON.stringify).join("\n") + "\n");
    for (const cycle of cycles) {
      await fs.writeFile(path.join(directory, "logs", `${cycle.cycle_id}.context.json`), JSON.stringify({
        version: 1, cycleId: cycle.cycle_id, project: "projects/journal-fixture",
        recordedAt: cycle.started_at, source: "runtime_context",
      }));
      await fs.writeFile(path.join(directory, "logs", `${cycle.cycle_id}.json`), JSON.stringify({
        result: `**第 ${cycle.cycle_number} 轮工作已完成。**\n\n本轮记录：保留历史并核对结果。`,
      }));
      await fs.writeFile(path.join(directory, "logs", `${cycle.cycle_id}.log`), `Fixture log ${cycle.cycle_number}\n<unsafe-is-text>\n`);
    }
    await fs.writeFile(path.join(directory, "memories", "consensus.md"), [
      "# Autonomous Company Consensus", "## Current Phase", "Validating", "## What We Did This Cycle",
      "- 已完成当前轮次验证。", "- <img src=x onerror=window.journalInjected=true>",
      "## Active Projects", "- Journal Fixture：本地预览", "## Next Action", "等待用户检查新界面。",
      "## Company State", "- Product: Journal Fixture，本地工作记录预览", "",
    ].join("\n"));
    await fs.mkdir(path.join(directory, "projects/journal-fixture"), { recursive: true });
    await fs.writeFile(path.join(directory, "projects/journal-fixture/.autonomous-company-project.json"), JSON.stringify({
      version: 1, project: "projects/journal-fixture", displayName: "Journal Fixture", description: "Local journal fixture",
      recordedAt: new Date().toISOString(), source: "project_metadata",
    }));
    await fs.writeFile(path.join(directory, ".autonomous-company.local"), "ACTIVE_PROJECT=projects/journal-fixture\nAUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n");
    await fs.writeFile(path.join(directory, ".auto-loop-state"), "STATUS=stopped\nENGINE=codex\nMODEL=gpt-6-astra\nLOOP_COUNT=3\n");
    const deliveryText = "# Browser fixture delivery\nThis document stays read-only.\n";
    const deliveryPath = "projects/journal-fixture/DELIVERY.md";
    await fs.writeFile(path.join(directory, deliveryPath), deliveryText);
    await fs.mkdir(path.join(directory, "logs/artifacts"), { recursive: true });
    const recordedAt = new Date().toISOString();
    await fs.writeFile(path.join(directory, "logs/artifacts/delivery.json"), JSON.stringify({
      version: 1, id: "a".repeat(32), kind: "document", project: "projects/journal-fixture",
      cycleId: cycles.at(-1).cycle_id, recordedAt, modifiedAt: recordedAt, source: "runner",
      path: deliveryPath, sha256: createHash("sha256").update(deliveryText).digest("hex"),
    }));
    const child = spawn(python, ['-u', path.join(repository, 'tests/browser/fixture-server.py'), '--repo', directory],
      { cwd: repository, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    let output = '';
    child.stderr.on('data', chunk => { output += chunk; });
    const closed = new Promise(resolve => child.once('close', resolve));
    const lines = createInterface({ input: child.stdout });
    try {
      const started = await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Center startup timed out: ${output}`)), 15000);
        const finish = (error, value) => { clearTimeout(timer); error ? reject(error) : resolve(value); };
        child.once('error', error => finish(error));
        child.once('exit', code => finish(new Error(`Center exited ${code}: ${output}`)));
        lines.once('line', line => { try { finish(null, JSON.parse(line)); } catch (error) { finish(error); } });
      });
      const journal = { ...started, directory,
        get detailUrl() { return `${this.url}/products/${this.entryId}`; },
        get apiUrl() { return `${this.url}/api/center/v1/entries/${this.entryId}/journal`; },
      };
      await use(journal);
    } finally {
      child.stdin.end();
      let timer;
      await Promise.race([closed, new Promise(resolve => { timer = setTimeout(() => { child.kill(); resolve(); }, 5000); })]);
      clearTimeout(timer);
      lines.close();
      if (path.dirname(path.resolve(directory)) !== path.resolve(os.tmpdir())
          || !path.basename(directory).startsWith("company-journal-browser-")) {
        throw new Error("Refusing cleanup outside the browser fixture directory");
      }
      await fs.rm(directory, { recursive: true, force: true });
    }
  },
});

test('spec compliance: manual tabs, compact mobile navigation and journal return state', async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  await expect(page.locator('#cycleNumber')).toHaveText('03');
  await page.locator('#tab-work').focus();
  await page.locator('#tab-work').press('ArrowRight');
  await expect(page.locator('#tab-usage')).toBeFocused();
  await expect(page.locator('#tab-work')).toHaveAttribute('aria-selected', 'true');
  await page.locator('#tab-usage').press('Enter');
  await expect(page.locator('#panel-usage')).toBeVisible();
  await page.locator('#tab-work').click();
  const history = page.locator('#historyList [data-disclosure]').first();
  await history.locator('.disclosure-trigger').click();
  await page.reload();
  await expect(page.locator('#historyList [data-disclosure]').first()).toHaveAttribute('open', '');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#productInfoJump')).toHaveCount(0);
  const back = await page.locator('#journalBackLink').boundingBox();
  const tabs = await page.locator('.topbar .ac-tabs-host').boundingBox();
  expect(back.y + back.height / 2).toBeCloseTo(tabs.y + tabs.height / 2, 1);
});

test('compact product information overlays the journal and restores the desktop sidebar', async ({ page, journal }) => {
  await page.setViewportSize({ width: 1000, height: 800 });
  await page.goto(journal.detailUrl);
  await expect(page.locator('#cycleNumber')).toHaveText('03');
  await expect(page.locator('#projectSidebar')).toBeHidden();
  const timeline = page.locator('.current-column');
  const before = await timeline.boundingBox();
  await page.locator('#projectInfoButton').click();
  await expect(page.locator('[role=dialog] #projectSidebar')).toBeVisible();
  const opened = await timeline.boundingBox();
  expect(opened.x).toBeCloseTo(before.x, 1);
  expect(Math.abs(opened.width - before.width)).toBeLessThan(1);
  await page.locator('[role=dialog]').press('Escape');
  await expect(page.locator('#projectInfoButton')).toBeFocused();
  await expect(page.locator('#projectSidebar')).toBeHidden();
  await page.locator('#projectInfoButton').click();
  await page.setViewportSize({ width: 1440, height: 800 });
  await expect(page.locator('[role=dialog]')).toHaveCount(0);
  await expect(page.locator('#projectSidebarHome #projectSidebar')).toBeVisible();
  await expect(page.locator('#projectInfoButton')).toBeHidden();
  await page.evaluate(() => {
    window.__resizeOverflow = [];
    const sample = () => {
      window.__resizeOverflow.push(document.documentElement.scrollWidth - innerWidth);
      window.__resizeFrame = requestAnimationFrame(sample);
    };
    window.__resizeFrame = requestAnimationFrame(sample);
  });
  for (const width of [360, 1440, 761, 760, 641, 640, 390]) {
    await page.setViewportSize({ width, height: 800 });
    const inset = await page.locator('.topbar').evaluate(node => node.querySelector('.brand').getBoundingClientRect().top - node.getBoundingClientRect().top);
    expect(inset).toBeCloseTo(12, 1);
  }
  await expect(page.locator('.sidebar-dock-motion')).toHaveCount(0);
  const overflow = await page.evaluate(() => {
    cancelAnimationFrame(window.__resizeFrame);
    return window.__resizeOverflow;
  });
  expect(overflow.length).toBeGreaterThan(0);
  expect(Math.max(...overflow)).toBeLessThanOrEqual(0);
});

test('spec compliance: disconnected logs preserve reading position, copy and source time', async ({ page, journal }) => {
  let failed = false;
  let log = Array.from({length: 250}, (_, index) => `record ${index} long log line`).join('\n');
  await page.route('**/api/center/v1/entries/*/resources/log-*?*', route => failed ? route.abort() : route.fulfill({contentType: 'text/plain', body: log}));
  await page.goto(journal.detailUrl);
  await expect(page.locator('#cycleNumber')).toHaveText('03');
  await page.locator('#tab-logs').click();
  await page.locator('#logSelect').selectOption('cycle-0001-fixture');
  await expect(page.locator('#logText')).toContainText('record 249');
  await page.locator('#logText').evaluate(node => { node.scrollTop = 190; });
  const top = await page.locator('#logText').evaluate(node => node.scrollTop);
  failed = true;
  await page.locator('#refreshLogButton').click();
  await expect(page.locator('#logStatus')).toContainText(/失败|Could not/);
  await expect(page.locator('#logStatus')).toContainText(/最后成功读取|Last successful read/);
  await expect(page.locator('#copyLogButton')).toBeEnabled();
  expect(await page.locator('#logText').evaluate(node => node.scrollTop)).toBe(top);
  await expect(page.locator('#logText')).toContainText('record 249');
  failed = false; log += '\nNEW RECORD';
  await page.locator('#refreshLogButton').click();
  await expect(page.locator('#newLogButton')).toBeVisible();
  expect(await page.locator('#logText').evaluate(node => node.scrollTop)).toBe(top);
  await page.locator('#newLogButton').click();
  await expect(page.locator('#logText')).toBeFocused();
  expect(await page.locator('#logText').evaluate(node => node.scrollHeight - node.clientHeight - node.scrollTop)).toBeLessThanOrEqual(4);
});

test('spec compliance: journal widths and mixed usage preserve all records', async ({ page, journal }, testInfo) => {
  await page.goto(journal.detailUrl);
  await expect(page.locator('#cycleNumber')).toHaveText('03');
  for (const width of [320, 359, 360, 390, 640, 641, 650, 651, 760, 761, 1000, 1001, 1064, 1440, 1450, 1800]) {
    await page.setViewportSize({width, height: 900});
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), `journal width ${width}`).toBeTruthy();
  }
  await page.setViewportSize({width: 320, height: 650});
  await page.screenshot({path: testInfo.outputPath('journal-320-fixture.png'), fullPage: true});
  await page.locator('#tab-usage').click();
  await expect(page.locator('#usageSource')).toContainText(/上次更新|Last updated/);
  await expect(page.locator('#usageRows tr')).toHaveCount(3);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({path: testInfo.outputPath('usage-320-fixture.png')});
  await page.locator('#tab-logs').click();
  await expect(page.locator('#refreshLogButton')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.setViewportSize({width: 532, height: 375});
  await page.addStyleTag({content: 'html { font-size: 32px !important; }'});
  await page.locator('#tab-work').click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.locator('#settingsButton').click();
  await expect(page.locator('#closeSettingsButton')).toBeInViewport();
  await page.locator('#closeSettingsButton').click();
});

test("journal renders source history and never treats a report as live telemetry", async ({ page, journal }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toContainText("03");
  await expect(page.locator("#cycleTitle")).toContainText("第 3 轮工作已完成");
  await expect(page.locator("body")).not.toContainText("等待用户检查新界面");
  await expect(page.locator("#projectSidebar #projectName")).toHaveText("Journal Fixture");
  await expect(page.locator(".topbar #projectName")).toHaveCount(0);
  const snapshot = (await (await page.request.get(journal.apiUrl)).json()).data;
  expect(snapshot.consensus).not.toHaveProperty("nextAction");
  await expect(page.locator("body")).toContainText(/只读|预览/);
  await expect(page.locator("body")).not.toContainText("本轮执行中");
  await expect(page.locator("#runtimeActionButton, #runtimeControls")).toHaveCount(0);
  await expect(page.locator("#readOnlyIndicator svg")).toHaveAttribute("data-lucide", "eye");
  await page.locator("#settingsButton").click();
  await expect(page.locator('#languageSelect, [data-i18n="openConsensus"]')).toHaveCount(0);
  await expect(page.locator('#settingsDialog a[href^="/docs/"]')).toHaveCount(4);
  await page.locator("#closeSettingsButton").click();
  expect(await page.evaluate(() => window.journalInjected)).toBeUndefined();
  expect(errors).toEqual([]);
});

test("stable identity keeps moved history and document access, then isolates a same-path replacement", async ({ page, journal }) => {
  await changeIdentityFixture(journal.directory, [
    "row = products.reserve_cycle(root, 'projects/journal-fixture', 'browser-identity-fixture', 1, 'fixture', 'no-model')",
    "products.update_cycle(root, row['cycleId'], 'completed')",
    "record_path = root / 'logs/artifacts/delivery.json'",
    "record = json.loads(record_path.read_text()); record['cycleId'] = row['cycleId']",
    "record_path.write_text(json.dumps(record))",
    "(root / 'logs' / (row['cycleId'] + '.json')).write_text(json.dumps({'result': 'Synthetic identity fixture report'}))",
    "(root / 'projects/journal-fixture').rename(root / 'projects/moved-fixture')",
    "products.relocate_identity(root, row['productId'], 'projects/moved-fixture')",
    "(root / '.autonomous-company.local').write_text('ACTIVE_PROJECT=projects/moved-fixture\\nAUTONOMOUS_COMPANY_LANGUAGE=en\\n')",
  ].join("\n"));
  await reimportProduct(page, journal);
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toHaveText("01");
  const document = page.locator('#projectSidebar a[href*="/resources/artifact-"]');
  await expect(document).toBeVisible();
  const snapshot = (await (await page.request.get(journal.apiUrl)).json()).data;
  expect(snapshot.cycles.find((cycle) => cycle.id === snapshot.latestProjectCycleId).projectId).toBe("projects/journal-fixture");
  const resource = new URL(await document.getAttribute('href'), journal.url).href;
  const moved = await page.request.get(resource);
  expect(moved.ok()).toBeTruthy();
  expect(await moved.text()).toContain("Browser fixture delivery");
  expect((await page.request.get(`${journal.url}/api/center/v1/entries/${journal.entryId}/resources/artifact-unregistered`)).ok()).toBeFalsy();
  await changeIdentityFixture(journal.directory, [
    "(root / 'projects/moved-fixture/.autonomous-company/identity.json').unlink()",
    "products.register_project(root, 'projects/moved-fixture')",
  ].join("\n"));
  await refreshRecords(page);
  await expect(document).toHaveCount(0);
  await expect(page.locator('#currentCycle')).not.toContainText('Synthetic identity fixture report');
  expect((await page.request.get(resource)).ok()).toBeFalsy();
  const originalEntry = journal.entryId;
  await reimportProduct(page, journal, originalEntry);
  expect(journal.entryId).not.toBe(originalEntry);
  await page.goto(journal.detailUrl);
  await expect(page.locator('#cycleNumber')).toHaveCount(0);
  await expect(page.locator('#projectSidebar a[href*="/resources/artifact-"]')).toHaveCount(0);
});

test("unproven legacy document remains inaccessible after identity registration", async ({ page, journal }) => {
  await changeIdentityFixture(journal.directory, "products.register_project(root, 'projects/journal-fixture')");
  await reimportProduct(page, journal);
  await page.goto(journal.detailUrl);
  await expect(page.locator("#projectSidebar")).toContainText("尚无可读取的成果文档");
  await expect(page.locator('#projectSidebar a[href*="/resources/artifact-"]')).toHaveCount(0);
  expect((await page.request.get(`${journal.url}/api/center/v1/entries/${journal.entryId}/resources/artifact-${"a".repeat(32)}`)).ok()).toBeFalsy();
});

test("relocated exploration keeps its recorded report and identity-bound document", async ({ page, journal }) => {
  await changeIdentityFixture(journal.directory, [
    "from cycle_reports import write_report",
    "from runtime_artifacts import write_context",
    "row = products.reserve_cycle(root, '', 'browser-exploration-fixture', 1, 'fixture', 'no-model')",
    "identity = products.register_project(root, 'projects/journal-fixture', row['cycleId'])",
    "write_context(root, row['cycleId'], '')",
    "write_report(root, row['cycleId'], {'title': 'Synthetic relocated exploration', 'summary': 'Synthetic report', 'phase': 'review', 'blocker': '', 'final': True}, 'projects/journal-fixture')",
    "products.update_cycle(root, row['cycleId'], 'completed')",
    "record_path = root / 'logs/artifacts/delivery.json'",
    "record = json.loads(record_path.read_text()); record['cycleId'] = row['cycleId']; record['productId'] = identity['id']",
    "record_path.write_text(json.dumps(record))",
    "(root / 'projects/journal-fixture').rename(root / 'projects/moved-fixture')",
    "products.relocate_identity(root, identity['id'], 'projects/moved-fixture')",
    "(root / '.autonomous-company.local').write_text('ACTIVE_PROJECT=projects/moved-fixture\\nAUTONOMOUS_COMPANY_LANGUAGE=en\\n')",
  ].join("\n"));
  await reimportProduct(page, journal);
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleTitle")).toHaveText("Synthetic relocated exploration");
  await expect(page.locator('#projectSidebar a[href*="/resources/artifact-"]')).toBeVisible();
  const snapshot = (await (await page.request.get(journal.apiUrl)).json()).data;
  const current = snapshot.cycles.find((cycle) => cycle.id === snapshot.latestProjectCycleId);
  expect(current.workReportStatus).toBe("valid");
  expect(current.workReport.project).toBe("projects/journal-fixture");
});

test("real static preview loads web assets and denies private same-origin reads", async ({ page, journal }) => {
  const project = path.join(journal.directory, "projects/journal-fixture");
  await fs.writeFile(path.join(project, "index.html"), '<!doctype html><title>Synthetic preview fixture</title><link rel="stylesheet" href="style.css"><h1>Synthetic fixture</h1><img src="image.svg"><script src="app.js"></script>');
  await fs.writeFile(path.join(project, "style.css"), "h1 { color: rgb(1, 2, 3); }");
  await fs.writeFile(path.join(project, "app.js"), "window.previewFixture = true;");
  await fs.writeFile(path.join(project, "image.svg"), '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4"/></svg>');
  await fs.writeFile(path.join(project, ".env"), "FAKE_SECRET=synthetic-only");
  const child = spawn(python, [path.join(repository, "scripts/core/runtime_artifacts.py"),
    "--root", journal.directory, "--project", "projects/journal-fixture", "preview"],
  { windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
  let output = "";
  child.stdout.on("data", (chunk) => { output += chunk; });
  let preview;
  try {
    await expect.poll(() => output).toMatch(/http:\/\/127\.0\.0\.1:\d+\//);
    const url = output.match(/http:\/\/127\.0\.0\.1:\d+\//)[0];
    await page.goto(url);
    await expect(page.locator("h1")).toHaveCSS("color", "rgb(1, 2, 3)");
    expect(await page.evaluate(() => window.previewFixture)).toBeTruthy();
    expect(await page.locator("img").evaluate((image) => image.complete && image.naturalWidth === 4)).toBeTruthy();
    for (const resource of ["/.env", "/.autonomous-company-health"]) {
      const status = await page.evaluate(async (resource) => (await fetch(resource)).status, resource);
      expect([403, 404]).toContain(status);
    }
    const folder = path.join(journal.directory, "logs/artifacts");
    for (const name of await fs.readdir(folder)) {
      const record = JSON.parse(await fs.readFile(path.join(folder, name), "utf8"));
      if (record.kind === "preview") preview = record;
    }
    expect(preview).toBeTruthy();
    const stopped = await fetch(`${url}.autonomous-company-stop`, { method: "POST", headers: { "X-Autonomous-Company-Preview": preview.token } });
    expect(stopped.status).toBe(204);
    await expect.poll(() => child.exitCode).toBe(0);
  } finally {
    if (child.exitCode === null) {
      child.kill();
      await new Promise((resolve) => child.once("exit", resolve));
    }
  }
});

test("history stays open after refresh and its log belongs to the selected cycle", async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  const row = page.locator("#historyList [data-disclosure]").first();
  await row.locator(".disclosure-trigger").click();
  await expect(row).toHaveAttribute("open", "");
  await refreshRecords(page);
  await expect(row).toHaveAttribute("open", "");
  await page.locator("#tab-logs").click();
  await page.locator("#logSelect").selectOption("cycle-0001-fixture");
  await expect(page.locator("#logText")).toContainText("Fixture log 1");
  await expect(page.locator("#logText")).not.toContainText("Fixture log 3");
});

test("usage preserves unknown coverage and artifacts open through the real server", async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toContainText("03");
  await page.locator("#tab-usage").click();
  await expect(page.locator("body")).toContainText(/部分|未知|不完整/);
  await page.locator("#tab-work").click();
  const delivery = page.locator('#projectSidebar a[href*="/resources/artifact-"]');
  await expect(delivery.first()).toBeVisible();
  const response = await page.request.get(new URL(await delivery.first().getAttribute("href"), journal.url).href);
  expect(response.ok()).toBeTruthy();
  expect(await response.text()).toContain("Browser fixture delivery");
  const write = await page.request.post(`${journal.url}/api/action/start`, { data: {} });
  expect(write.status()).toBe(404);
});

test("failed refresh remains visible and recovers without losing the journal", async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toContainText("03");
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({
    status: 503, contentType: "application/json", body: JSON.stringify({ ok: false, error: "Unavailable" }),
  }));
  await refreshRecords(page);
  await expect(page.getByRole("alert")).toBeVisible();
  await page.unroute("**/api/center/v1/entries/*/journal?*");
  await refreshRecords(page);
  await expect(page.getByRole("alert")).toBeHidden();
  await expect(page.locator("#cycleNumber")).toContainText("03");
});

test("narrow layout and settings remain usable by keyboard", async ({ page, journal }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toContainText("03");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.locator("#settingsButton").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(page.locator("#settingsButton")).toBeFocused();
});

test("empty archive follows English preference and remains navigable", async ({ page, journal }) => {
  await fs.writeFile(path.join(journal.directory, "logs", "usage.jsonl"), "");
  await setLanguage(page, journal, "en");
  await page.goto(journal.detailUrl);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByRole("heading", { name: "No cycle records yet" })).toBeVisible();
  await page.locator("#tab-logs").click();
  await expect(page.locator("#logSelect option")).toHaveCount(0);
  await expect(page.locator("#logStatus")).toContainText(/empty|no log/i);
  await expect(page.locator("#copyLogButton")).toBeDisabled();
  await expect(page.locator("#refreshLogButton")).toBeDisabled();
  await page.locator("#tab-usage").click();
  await expect(page.locator("#usageSummary")).toContainText("no usage records");
});

test("failed latest cycle never inherits an earlier consensus as its results", async ({ page, journal }) => {
  await fs.appendFile(path.join(journal.directory, "logs", "usage.jsonl"), JSON.stringify({
    schema_version: 1, kind: "cycle_usage", project: "projects/journal-fixture", cycle_id: "cycle-0004-failed",
    cycle_number: 4, started_at: new Date().toISOString(), ended_at: new Date().toISOString(),
    status: "failed", exit_code: 1, engine: "codex", model: "gpt-6-astra", usage: {},
  }) + "\n");
  await fs.writeFile(path.join(journal.directory, "logs/cycle-0004-failed.context.json"), JSON.stringify({
    version: 1, cycleId: "cycle-0004-failed", project: "projects/journal-fixture",
    recordedAt: new Date().toISOString(), source: "runtime_context",
  }));
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toContainText("04");
  await expect(page.locator("#currentCycle")).toContainText("执行失败");
  await expect(page.locator("#currentCycle")).not.toContainText("已完成当前轮次验证");
});

test("product timeline shows continuous authoritative numbers and exploration by default", async ({ page, journal }) => {
  const data = (await (await page.request.get(journal.apiUrl)).json()).data;
  const template = data.cycles[0];
  const cycle = (id, number, identityKind, status, summary, projectStatus = "current") => ({
    ...template, id, number, sequenceNumber: identityKind === "product" ? number + 3 : identityKind === "exploration" ? number : null, identityKind, numbering: "persistent", projectStatus, status,
    active: false, summary, report: summary, workReport: null, workReportStatus: null,
    startedAt: new Date(Date.now() - number * 60000).toISOString(),
    endedAt: new Date(Date.now() - number * 60000 + 30000).toISOString(),
  });
  const products = [4, 3, 2, 1].map((number) => cycle(`product-${number}`, number, "product", "completed", `Product record ${number}`));
  const exploration = [
    cycle("explore-3", 3, "exploration", "completed", "Exploration report 3"),
    cycle("explore-2", 2, "exploration", "failed", "Exploration report 2"),
    cycle("explore-1", 1, "exploration", "unknown", "Exploration report 1", "unknown"),
  ];
  const legacy = cycle("legacy-9", 9, undefined, "unknown", "Legacy unknown record", "unknown");
  legacy.numbering = "legacy";
  delete legacy.identityKind;
  data.cycles = [...products, ...exploration, legacy];
  data.latestProjectCycleId = "product-4";
  data.cycleNumbering = { mode: "persistent", hasLegacy: true };
  await setLanguage(page, journal, "en");
  data.language = "en";
  data.languageState = null;
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({ json: envelope(data) }));
  await page.goto(journal.detailUrl);

  await expect(page.locator("#cycleNumber")).toHaveText("07");
  await expect(page.locator("#historyList .history-number-value")).toHaveText(["06", "05", "04", "03", "02", "01", "09"]);
  await expect(page.locator("#historyList .history-row[open]")).toHaveCount(0);
  await expect(page.locator("#olderButton, #explorationSection")).toHaveCount(0);
  const explorationRows = page.locator('#historyList .history-row[data-cycle-id^="explore-"]');
  await expect(explorationRows).toHaveCount(3);
  await expect(explorationRows.locator(".disclosure-trigger .progress-completed")).toHaveCount(1);
  await expect(explorationRows.locator(".disclosure-trigger .progress-failed")).toHaveCount(1);
  await expect(explorationRows.locator(".disclosure-trigger .progress-unknown")).toHaveCount(1);
  const explorationRow = explorationRows.first();
  await expect(explorationRow).toBeVisible();
  await expect(explorationRow.locator(".disclosure-trigger")).toContainText("Pre-product exploration");
  await explorationRow.locator(".disclosure-trigger").click();
  await expect(explorationRow).toHaveAttribute("open", "");
  await expect(explorationRow.locator(".history-content")).toContainText("Exploration report 3");
  await expect(explorationRow.locator(".cycle-log-link")).toBeVisible();

  await refreshRecords(page);
  await expect(explorationRow).toHaveAttribute("open", "");

  const legacyRow = page.locator('#historyList .history-row[data-cycle-id="legacy-9"]');
  await expect(legacyRow).toBeVisible();
  await expect(legacyRow.locator(".progress-unknown")).toHaveCount(1);
  await legacyRow.locator(".disclosure-trigger").click();
  await expect(legacyRow.locator(".history-content")).toContainText("Legacy unknown record");
  await page.setViewportSize({ width: 360, height: 900 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});

test("exploration-only archives keep the original current and history timeline", async ({ page, journal }) => {
  const data = (await (await page.request.get(journal.apiUrl)).json()).data;
  data.cycles = data.cycles.map((cycle, index) => ({
    ...cycle, identityKind: "exploration", projectStatus: "current",
    summary: `Exploration-only record ${3 - index}`, report: `Exploration-only record ${3 - index}`,
  }));
  data.latestProjectCycleId = data.cycles[0].id;
  await setLanguage(page, journal, "en");
  data.language = "en";
  data.languageState = null;
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({ json: envelope(data) }));
  await page.goto(journal.detailUrl);
  await expect(page.locator("#cycleNumber")).toHaveText("03");
  await expect(page.locator("#currentCycle")).toContainText("Pre-product exploration");
  await expect(page.locator("#historyList .history-number-value")).toHaveText(["02", "01"]);
  await expect(page.locator("#explorationSection")).toHaveCount(0);
});


test("cycle timeline preserves disclosures, keyboard focus and selected logs across changed data", async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  const summary = page.locator("#historyList > [data-disclosure] .disclosure-trigger").first();
  await summary.click();
  await summary.focus();
  const latest = path.join(journal.directory, "logs/cycle-0003-fixture.json");
  await fs.writeFile(latest, JSON.stringify({ result: "Changed report after refresh" }));
  await page.evaluate(() => document.getElementById("refreshButton").click());
  await expect(page.locator("#cycleTitle")).toHaveText("Changed report after refresh");
  await expect(page.locator("#historyList > [data-disclosure]").first()).toHaveAttribute("open", "");
  await expect(summary).toBeFocused();
  await expect(page.locator(".current-cycle")).toHaveAttribute("aria-current", "step");
  expect(await page.locator(".current-cycle").evaluate((node) => getComputedStyle(node, "::before").width)).toBe("2px");
  await page.locator("#tab-logs").click();
  await page.locator("#logSelect").selectOption("cycle-0001-fixture");
  await fs.writeFile(latest, JSON.stringify({ result: "Another changed report" }));
  await refreshRecords(page);
  await expect(page.locator("#logSelect")).toHaveValue("cycle-0001-fixture");
  await expect(page.locator("#logText")).toContainText("Fixture log 1");
});

test("current round expands in place and keeps its collapsed state after refresh", async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  const heading = page.locator('.current-cycle-heading');
  await expect(heading).toHaveAttribute('aria-expanded', 'true');
  await heading.click();
  await expect(heading).toHaveAttribute('aria-expanded', 'false');
  await expect(page.locator('.current-cycle-content')).toBeHidden();
  await expect(page.locator('#tab-work')).toHaveAttribute('aria-selected', 'true');
  await refreshRecords(page);
  await expect(heading).toHaveAttribute('aria-expanded', 'false');
  await heading.press('Enter');
  await expect(page.locator('.current-cycle-content')).toBeVisible();
  await expect(page.locator('.project-runtime .runtime-details dd')).toHaveCount(9);
  await expect(page.locator('.brand')).toHaveAttribute('href', '/center');
});

test("all cycle headings share full-row interaction and retain height when toggled", async ({ page, journal }) => {
  await page.goto(journal.detailUrl);
  await expect(page.locator('#workspaceProjectName')).toHaveText('Journal Fixture');
  for (const width of [1597, 390]) {
    await page.setViewportSize({ width, height: 919 });
    for (const row of [page.locator('.current-cycle'), page.locator('#historyList .cycle-row').first()]) {
      const heading = row.locator('.disclosure-trigger');
      const before = await heading.boundingBox();
      const rowBox = await row.boundingBox();
      expect(before.width).toBeCloseTo(rowBox.width, 0);
      const expanded = await heading.getAttribute('aria-expanded');
      await heading.click({ position: { x: 10, y: before.height / 2 } });
      await expect(heading).toHaveAttribute('aria-expanded', expanded === 'true' ? 'false' : 'true');
      expect((await heading.boundingBox()).height).toBe(before.height);
      await heading.press('Enter');
      expect((await heading.boundingBox()).height).toBe(before.height);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
});

test("unnamed projects use a preset title in the workspace tab", async ({ page, journal }) => {
  const data = (await (await page.request.get(journal.apiUrl)).json()).data;
  data.project = { ...data.project, displayName: '', name: '' };
  data.entry = null;
  await page.route('**/api/center/v1/entries/*/journal?*', route => route.fulfill({ json: envelope(data) }));
  await page.goto(journal.detailUrl);
  await expect(page.locator('#workspaceProjectName')).toHaveText('未命名项目');
});

test("compact records preserve failures and unknowns while hiding technical details in both languages", async ({ page, journal }) => {
  const data = (await (await page.request.get(journal.apiUrl)).json()).data;
  const current = data.cycles[0];
  current.checkStatus = "completed";
  current.latestCheck = { id: "check-fixture", cycleId: current.id, state: "completed", evidenceStatus: "completed", available: false,
    source: "runner", adapter: "junit", reportStatus: "fresh", freshness: "fresh", exitCode: 1,
    tests: { tests: 12, failures: 2, errors: 1, skipped: 3 }, recordedAt: data.generatedAt,
    command: ["python", "test_" + "long".repeat(80) + ".py"] };
  const command = "node --test " + "long/path/".repeat(40);
  current.events = [
    { kind: "files", observedAt: data.generatedAt, paths: ["older.txt"] },
    { kind: "command", phase: "started", itemId: "test", observedAt: data.generatedAt, command },
    { kind: "files", observedAt: data.generatedAt, paths: ["recent.txt"] },
    { kind: "command", phase: "completed", itemId: "test", observedAt: data.generatedAt, command, exitCode: 1 },
    { kind: "turn.completed", observedAt: data.generatedAt },
    { kind: "process.exited", observedAt: data.generatedAt },
  ];
  data.artifacts = [{ kind: "preview", state: "stopped", evidenceStatus: "stale", available: false }];
  await setLanguage(page, journal, "en");
  let language = "en";
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({ json: envelope({ ...data, language, languageState: null }) }));
  await page.goto(journal.detailUrl);
  await expect(page.locator("#currentCycle .record-check")).toContainText("6 passed · 2 failed · 1 errors · 3 skipped");
  await expect(page.locator("#currentCycle .record-check .progress-failed")).toHaveCount(1);
  await expect(page.locator("#currentCycle")).not.toContainText(command);
  await expect(page.locator("#currentCycle .report-disclosure, #currentCycle .event-command")).toHaveCount(0);
  await expect(page.locator("#projectSidebar")).not.toContainText("Preview ended");
  await expect(page.locator("#projectSidebar")).not.toContainText("File changed or missing");
  for (const locale of ["en", "zh-CN"]) {
    language = locale;
    await setLanguage(page, journal, locale);
    await refreshRecords(page);
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    for (const width of [1280, 360]) {
      await page.setViewportSize({ width, height: 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    }
  }
  current.latestCheck = null;
  current.checkStatus = "unregistered";
  await refreshRecords(page);
  await expect(page.locator("#currentCycle .record-check")).toContainText("暂无已登记检查");
  await expect(page.locator("#currentCycle .record-check")).not.toContainText("通过");
  current.latestCheck = { state: "completed", evidenceStatus: "missing", exitCode: 0, tests: { tests: 7, failures: 0, errors: 0, skipped: 0 } };
  current.checkStatus = "stale";
  await refreshRecords(page);
  await expect(page.locator("#currentCycle .record-check")).toContainText("过期");
  await expect(page.locator("#currentCycle .record-check")).not.toContainText("7 项通过");
  current.projectStatus = "unknown";
  data.project.id = null;
  await refreshRecords(page);
  await expect(page.locator("#currentCycle .record-check")).toHaveCount(0);
});

test("running elapsed freezes on disconnect and rejects older snapshots", async ({ page, journal }) => {
  const data = (await (await page.request.get(journal.apiUrl)).json()).data;
  data.readOnly = false;
  data.runtime = { ...data.runtime, available: true, processState: "running", state: "running", elapsedReliable: true, elapsedSeconds: 60 };
  data.cycles[0] = { ...data.cycles[0], active: true, status: "running", endedAt: null };
  await setLanguage(page, journal, "en");
  data.language = "en"; data.languageState = null;
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({ json: envelope(data) }));
  await page.goto(journal.detailUrl);
  await expect(page.locator(".live-elapsed")).toContainText("Running for 1m");
  await page.locator("#settingsButton").click();
  await page.locator("#autoRefresh-control").uncheck();
  await page.locator("#closeSettingsButton").click();
  await page.unroute("**/api/center/v1/entries/*/journal?*");
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({ status: 503, json: { ok: false } }));
  await refreshRecords(page);
  await expect(page.locator("#connectionError")).toBeVisible();
  await expect(page.locator(".live-elapsed")).toHaveText("Elapsed time unconfirmed");
  await expect(page.locator("#refreshStatus")).toContainText("Last updated");
  await page.unroute("**/api/center/v1/entries/*/journal?*");
  await page.route("**/api/center/v1/entries/*/journal?*", (route) => route.fulfill({ json: envelope({ ...data,
    generatedAt: new Date(Date.parse(data.generatedAt) - 1000).toISOString(), cycles: [] }) }));
  await refreshRecords(page);
  await expect(page.locator("#cycleNumber")).toHaveText("03");
  await expect(page.locator("#connectionError")).toBeVisible();
});


test("earlier check evidence stays visible without replacing the latest failure", async ({ page, journal }) => {
  const data = (await (await page.request.get(journal.apiUrl)).json()).data;
  const current = data.cycles[0];
  const older = { id: 'older-check', state: 'completed', evidenceStatus: 'completed', available: true, freshness: 'fresh', reportStatus: 'fresh', exitCode: 0,
    tests: { tests: 2, failures: 0, errors: 0, skipped: 0 }, recordedAt: current.startedAt, path: 'docs/old-check.xml', url: `/api/center/v1/entries/${journal.entryId}/resources/artifact-old-check?sourceId=${journal.sourceId}` };
  const latest = { ...older, id: 'latest-check', path: 'docs/latest-check.xml', exitCode: 1, tests: { tests: 2, failures: 1, errors: 0, skipped: 0 } };
  current.latestCheck = latest; current.checks = [latest, older]; current.checkStatus = "completed";
  await setLanguage(page, journal, 'en');
  await page.route('**/api/center/v1/entries/*/journal?*', route => route.fulfill({ json: envelope({ ...data, language: 'en', languageState: null }) }));
  await page.goto(journal.detailUrl);
  await expect(page.locator('#currentCycle .record-check')).toContainText('1 failed');
  await expect(page.locator('#currentCycle .record-check-history')).toHaveCount(1);
  await expect(page.locator('#currentCycle .record-check-history')).toContainText('2 passed');
  await expect(page.locator('#currentCycle .record-check-history a')).toHaveAttribute('href', /resources\/artifact-old-check\?sourceId=/);
  for (const state of ['running', 'interrupted', 'stale']) {
    current.checkStatus = state; current.latestCheck = { ...latest, evidenceStatus: state, state };
    await refreshRecords(page);
    await expect(page.locator('#currentCycle .record-check-history')).toContainText('2 passed');
    await expect(page.locator('#currentCycle .record-check-history')).toHaveAttribute('data-status', 'completed');
  }
});
