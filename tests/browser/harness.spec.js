import { test, expect } from './fixtures.js';

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
