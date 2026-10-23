import { test, expect } from './fixtures.js';

async function presentCycle(page, center, change) {
  const adapt = async route => {
    if (new URL(route.request().url()).searchParams.has('component')) return route.continue();
    const response = await route.fetch(), payload = await response.json(), data = payload.data;
    const current = data.cycles ? data.cycles.find(row => row.id === data.currentCycleId) : data;
    change(current, data);
    await route.fulfill({ response, json: payload });
  };
  await page.route(`**/api/center/v1/entries/${center.entryId}/journal?*`, adapt);
  await page.route(`**/api/center/v1/entries/${center.entryId}/records/*?*`, adapt);
}

test('confirmed record times render without legacy duration uncertainty or an empty check row', async ({ page, center }) => {
  const confirmed = '2026-10-23T07:27:43+08:00';
  await presentCycle(page, center, (cycle, data) => {
    const suffix = `?sourceId=${data.sourceId}&projectionVersion=2&sourceBindingVersion=${data.sourceBindingVersion}&projectionEpoch=${data.projectionEpoch}`;
    Object.assign(cycle, { harnessVersion: 2, protocolState: 'closed', outcome: 'completed', status: 'completed', active: false,
      durationReliable: false, time: { reliability: 'reliable', executionSeconds: 255, recoverySeconds: 0, totalSeconds: 258 },
      latestCheck: null, checks: [], checkStatus: 'unregistered',
      qualityApplicability: [{ verdict: 'passed', workKinds: ['research'], confirmedAt: confirmed }],
      evidenceRefs: [{ evidenceId: 'document-proof', label: 'Confirmed document', confirmedAt: confirmed,
        url: `/api/center/v1/entries/${center.entryId}/resources/document-proof${suffix}` }] });
    cycle.partitions.checks = { ...cycle.partitions.checks, status: 'missing', freshness: 'unknown' };
  });
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#currentCycle .record-quality time')).toHaveAttribute('datetime', confirmed);
  await expect(page.locator('#currentCycle .record-quality time')).toHaveAttribute('title', /Record confirmed at/);
  await expect(page.locator('#currentCycle .record-document time').last()).toHaveAttribute('datetime', confirmed);
  await expect(page.locator('#currentCycle .cycle-meta')).toContainText('Execution 255');
  await expect(page.locator('#currentCycle .cycle-meta')).not.toContainText('Duration unconfirmed');
  await expect(page.locator('#currentCycle .record-check')).toHaveCount(0);
  await expect(page.locator('#currentCycle .cycle-log-link')).toBeVisible();
});

test('collection failure retains its report and check warning with a scoped human pause', async ({ page, center }) => {
  await presentCycle(page, center, (cycle, data) => {
    Object.assign(cycle, { harnessVersion: 2, protocolState: 'closed', outcome: 'failed', status: 'failed', active: false,
      executionIssue: { code: 'COLLECTION_UNCONFIRMED' }, latestCheck: null, checks: [], checkStatus: 'unregistered' });
    cycle.partitions.checks = { ...cycle.partitions.checks, status: 'unavailable', errorCode: 'COLLECTION_UNCONFIRMED' };
    if (data.cycles) {
      data.runtime = { ...data.runtime, state: 'paused', available: true, pauseReason: 'human_required' };
      data.entry = { ...data.entry, runtimeId: null, executionSummary: { state: 'read_only' },
        readonlyObservation: { state: 'paused', scoped: true, readOnly: true, processState: 'running',
          liveConfirmedAt: new Date().toISOString(), pauseReason: 'human_required' } };
    }
  });
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#currentCycle .report-intro')).not.toBeEmpty();
  await expect(page.locator('#currentCycle .report-section')).toContainText('Artifact collection did not complete');
  await expect(page.locator('#currentCycle .record-check')).toContainText('Check records unavailable');
  await expect(page.locator('#runtimeEvidence')).toContainText('Human attention required');
  await expect(page.locator('#sidebarRuntimeState')).toHaveText('Paused');
});

for (const scenario of [{ name: 'truncated success', failed: 0, truncated: true }, { name: 'gapped failure', failed: 1, gaps: [{ after: 2 }] }]) {
  test(`partial checks retain known counts without hiding ${scenario.name}`, async ({ page, center }) => {
    await presentCycle(page, center, cycle => {
      cycle.latestCheck = { id: 'partial-check', state: 'completed', evidenceStatus: 'completed', exitCode: scenario.failed,
        tests: { tests: 3, failures: scenario.failed, errors: 0, skipped: 0 } };
      cycle.checks = [cycle.latestCheck]; cycle.checkStatus = 'completed';
      cycle.partitions.checks = { ...cycle.partitions.checks, revision: 10, status: 'partial', freshness: 'fresh',
        truncated: scenario.truncated || false, gaps: scenario.gaps || [] };
    });
    await page.goto(`${center.url}/products/${center.entryId}`);
    const summary = page.locator('#currentCycle .record-check');
    await expect(summary).toContainText(`${3 - scenario.failed} passed`);
    await expect(summary).toContainText('Check collection is incomplete');
    await expect(summary).toHaveAttribute('data-status', scenario.failed ? 'failed' : 'unknown');
    if (scenario.failed) await expect(summary).toContainText('1 failed');
  });
}

test('v2 reports keep advancing through independent usage and media failures', async ({ page, center }) => {
  let reports = 0;
  await page.route(`**/api/center/v1/entries/${center.entryId}/usage?*`, route => route.fulfill({ status: 503, json: { code: 'CONTEXT_UNAVAILABLE' } }));
  await page.route(`**/api/center/v1/entries/${center.entryId}/journal?*`, async route => {
    const url = new URL(route.request().url());
    if (url.searchParams.get('component') === 'media') return route.fulfill({ status: 503, json: { code: 'CONTEXT_UNAVAILABLE' } });
    const response = await route.fetch(); const payload = await response.json();
    expect(payload.data.projectionVersion).toBe(2);
    return route.fulfill({ response, json: payload });
  });
  await page.route(`**/api/center/v1/entries/${center.entryId}/records/*?*`, async route => {
    const response = await route.fetch(); const payload = await response.json();
    reports += 1;
    const current = payload.data;
    if (reports > 1) {
      current.workReport.title = 'Fresh report after usage failure';
      current.partitions.report.revision += reports;
    }
    return route.fulfill({ response, json: payload });
  });
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#cycleTitle')).toContainText('Fixture round 6');
  await page.locator('#settingsButton').click();
  await expect(page.locator('#refreshButton')).toBeEnabled();
  await page.locator('#refreshButton').click();
  await page.locator('#closeSettingsButton').click();
  await expect(page.locator('#cycleTitle')).toHaveText('Fresh report after usage failure');
  await expect(page.locator('#connectionError')).toBeHidden();
  await page.locator('#tab-usage').click();
  await expect(page.locator('#usageSummary')).toContainText('Usage unavailable');
});

test('one logical cycle exposes separate execution logs and an honest handoff state', async ({ page, center }) => {
  await page.route(`**/api/center/v1/entries/${center.entryId}/journal?*`, async route => {
    if (new URL(route.request().url()).searchParams.has('component')) return route.continue();
    const response = await route.fetch(), payload = await response.json(), data = payload.data;
    const current = data.cycles.find(cycle => cycle.id === data.currentCycleId);
    const suffix = `?sourceId=${data.sourceId}&projectionVersion=2&sourceBindingVersion=${data.sourceBindingVersion}&projectionEpoch=${data.projectionEpoch}`;
    Object.assign(current, { harnessVersion: 2, protocolState: 'closed', outcome: 'partial', status: 'handoff', active: false,
      activeAttemptId: null, objective: 'Review one outcome', workKind: 'review', logAvailable: true,
      attempts: [1, 2].map(number => ({ attemptId: `fixture-attempt-${number}`, status: 'exited', startedAt: current.startedAt,
        logUrl: `/api/center/v1/entries/${center.entryId}/resources/fixture-attempt-${number}${suffix}` })) });
    return route.fulfill({ response, json: payload });
  });
  await page.route('**/resources/fixture-attempt-*', route => route.fulfill({ contentType: 'text/plain', body: route.request().url().includes('attempt-1?') ? 'First execution output' : 'Second execution output' }));
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#currentCycle')).toContainText('Handed off');
  await page.locator('#currentCycle .cycle-log-link').click();
  await expect(page.locator('#logText')).toContainText('Second execution output');
  await page.locator('#logSelect').selectOption('fixture-attempt-1');
  await expect(page.locator('#logText')).toContainText('First execution output');
  await expect(page.locator('#logSelect option[value="fixture-attempt-2"]')).toHaveText(/Attempt 2/);
  await expect(page.locator('#currentCycle')).toHaveCount(1);
});

test.describe('bounded history', () => {
  test.use({ centerCycles: 36, centerExplorationCycles: 3 });
  test('recent polling does not traverse historical pages; earlier records load on demand', async ({ page, center }) => {
    let historyReads = 0;
    page.on('request', request => { const url = new URL(request.url()); if (url.pathname.endsWith('/journal') && url.searchParams.has('before')) historyReads += 1; });
    await page.goto(`${center.url}/products/${center.entryId}`);
    await expect(page.locator('.cycle-row')).toHaveCount(20);
    expect(historyReads).toBe(0);
    await page.locator('.history-more').click();
    await expect(page.locator('.cycle-row')).toHaveCount(39);
    expect(historyReads).toBe(1);
    await expect(page.locator('.history-more')).toHaveCount(0);
    await expect(page.locator('#cycleNumber')).toHaveText('39');
    await page.locator('#tab-usage').click();
    await expect(page.locator('#usageRows tr')).toHaveCount(39);
  });
});

test.describe('legacy lazy details', () => {
  test.use({ centerLegacyInterrupted: true });
  test('event-only reports and bound documents survive light polling and scoped detail reloads', async ({ page, center }) => {
    let detailReads = 0;
    page.on('request', request => { if (new URL(request.url()).pathname.includes('/records/')) detailReads += 1; });
    await page.goto(`${center.url}/products/${center.entryId}`);
    await expect(page.locator('#currentCycle .report-intro')).toHaveText('Actual interrupted legacy report');
    const document = page.locator('#currentCycle .artifact-link', { hasText: 'DELIVERY.md' });
    await expect(document).toHaveCount(1);
    expect(await document.getAttribute('href')).toContain('sourceBindingVersion=');
    expect(detailReads).toBe(1);
    await page.locator('#settingsButton').click();
    await page.locator('#refreshButton').click();
    await page.locator('#closeSettingsButton').click();
    await expect.poll(() => detailReads).toBe(2);
    await expect(page.locator('#currentCycle .report-intro')).toHaveText('Actual interrupted legacy report');
    await expect(document).toHaveCount(1);
    const response = await page.request.get(new URL(await document.getAttribute('href'), center.url).href);
    expect(await response.text()).toBe('Bound legacy delivery evidence');
  });
});

test.describe('late historical accounting', () => {
  test.use({ centerCycles: 36 });
  test('old loaded usage is marked stale and a successful detail read installs its late accounting', async ({ page, center }) => {
    let late = false, historyReads = 0;
    page.on('request', request => { const url = new URL(request.url()); if (url.pathname.endsWith('/journal') && url.searchParams.has('before')) historyReads += 1; });
    await page.route(`**/api/center/v1/entries/${center.entryId}/records/${center.firstCycleId}?*`, async route => {
      const response = await route.fetch(), payload = await response.json();
      if (late) {
        payload.data.usage.totalTokens += 800; payload.data.costUsd = 8.5; payload.data.costStatus = 'reported';
        payload.data.partitions.usage.revision += 1;
      }
      await route.fulfill({ response, json: payload });
    });
    await page.route(`**/api/center/v1/entries/${center.entryId}/usage?*`, async route => {
      const response = await route.fetch(), payload = await response.json();
      if (late) {
        payload.data.usage.totalTokens += 800;
        const group = payload.data.groups.find(group => group.cycleId === center.firstCycleId);
        group.usage.totalTokens += 800;
        payload.data.partitions.usage.revision += 1;
      }
      await route.fulfill({ response, json: payload });
    });
    await page.goto(`${center.url}/products/${center.entryId}`);
    await page.locator('#settingsButton').click();
    await page.locator('#autoRefresh-control').uncheck();
    await page.locator('#closeSettingsButton').click();
    await page.locator('.history-more').click();
    await expect(page.locator('.cycle-row')).toHaveCount(36);
    late = true;
    await page.locator('#settingsButton').click();
    await page.locator('#refreshButton').click();
    await page.locator('#closeSettingsButton').click();
    await page.locator('#tab-usage').click();
    const old = page.locator(`#usageRows tr[data-cycle-id="${center.firstCycleId}"]`);
    await expect(page.locator('#usageSummary')).toContainText('810');
    await expect(old.locator('td').nth(5)).toHaveText('10');
    await expect(old.locator('td').last()).toHaveText('Not refreshed');
    await page.locator('#tab-work').click();
    await page.locator('#historyList [data-disclosure]').last().locator('.disclosure-trigger').click();
    await page.locator('#tab-usage').click();
    await expect(old.locator('td').nth(5)).toHaveText('810');
    await expect(old.locator('td').last()).not.toHaveText('Not refreshed');
    expect(historyReads).toBe(1);
  });
});
