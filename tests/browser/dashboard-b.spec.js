import { test, expect } from './fixtures.js';
import { mkdir, writeFile } from 'node:fs/promises';


async function openCenter(page, center) {
  await page.goto(`${center.url}/center`);
  await expect(page.locator('#observedAt')).not.toBeEmpty();
}


const envelope = data => ({ schemaVersion: 1, revision: 1, centerId: 'fixture', observedAt: new Date().toISOString(), data });

test('B preflight failure preserves original groups and never creates a batch', async ({ page, center }, info) => {
  let batches = 0;
  page.on('request', request => { if (request.method() === 'POST' && request.url().endsWith('/explorations/batch')) batches++; });
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  const group = page.locator('.work-group').first();
  await group.locator('[name=model]').fill('fixture-missing-dependency');
  await group.locator('[name=direction]').fill('Keep this direction');
  await group.locator('[name=count]').fill('3');
  await page.locator('#newWorkForm [type=submit]').click();
  await expect(page.locator('#newWorkForm .form-status')).toContainText('Checks failed', { timeout: 15000 });
  await expect(group.locator('[name=direction]')).toHaveValue('Keep this direction');
  await expect(group.locator('[name=count]')).toHaveValue('3');
  await expect(page.locator('#newWorkForm [type=submit]')).toBeEnabled();
  expect(batches).toBe(0);
  await page.screenshot({ path: info.outputPath('preflight-preserved.png') });
});

test('B a delayed preflight cannot submit a changed draft', async ({ page, center }) => {
  let pending, batches = 0;
  await page.route('**/api/center/v1/preflight', route => { pending = route; });
  page.on('request', request => { if (request.method() === 'POST' && request.url().endsWith('/explorations/batch')) batches++; });
  await openCenter(page, center); await page.locator('#newWorkButton').click();
  await page.locator('.work-group [name=model]').fill('first');
  await page.locator('#newWorkForm [type=submit]').click();
  await expect.poll(() => Boolean(pending)).toBe(true);
  await page.locator('.work-group [name=model]').fill('second');
  await pending.fulfill({ json: envelope({ ready: true, checks: [], environmentRevision: 0 }) });
  await expect(page.locator('#newWorkForm [type=submit]')).toBeEnabled();
  await expect(page.locator('.work-group [name=model]')).toHaveValue('second');
  expect(batches).toBe(0);
});

test('B environment is explicit and late check cannot overwrite a reopened dialog', async ({ page, center }) => {
  const environment = { domain: null, revision: 0, candidates: [{ id: 'wsl:test', label: 'Test Linux', domain: { platform: 'wsl', distribution: 'Test Linux' } }], checks: [] };
  await page.route('**/api/center/v1/environment', route => route.fulfill({ json: envelope(environment) }));
  let pending, body;
  await page.route('**/api/center/v1/environment/check', route => { pending = route; body = route.request().postDataJSON(); });
  await openCenter(page, center); await page.locator('#profileButton').click(); await page.getByRole('menuitem', { name: 'Runtime environment' }).click();
  await page.locator('#environmentForm [name=user]').fill('chosen-user');
  await page.locator('#environmentCheck').click(); await expect.poll(() => Boolean(pending)).toBe(true);
  expect(body.domain).toEqual({ platform: 'wsl', distribution: 'Test Linux', user: 'chosen-user' });
  await page.locator('#environmentForm .dialog-close').click();
  await page.locator('#profileButton').click(); await page.getByRole('menuitem', { name: 'Runtime environment' }).click();
  await expect(page.locator('#environmentCheck')).toBeEnabled();
  await pending.fulfill({ json: envelope({ ready: false, checks: [{ ok: false, message: 'Obsolete result' }], revision: 0 }) });
  await expect(page.locator('#environmentChecks')).not.toContainText('Obsolete result');
  await expect(page.locator('#environmentCheck')).toBeEnabled();
});

test('B zero results retain filters and no-rounds is distinct', async ({ page, center }) => {
  await page.route('**/api/center/v1/entries?*', route => route.fulfill({ json: envelope({ items: [{ entryId: 'empty-rounds', kind: 'exploration', displayName: 'No rounds fixture', availability: 'available', cycleNumber: null, latestCycleStatus: 'unknown', executionSummary: { state: 'ended' } }], total: 1, nextCursor: null }) }));
  await openCenter(page, center);
  await expect(page.locator('#productRows')).toContainText('No rounds fixture');
  await page.locator('#productSearch').fill('no-such-product');
  await expect(page.locator('#productRows .product-row')).toHaveCount(0);
  await expect(page.getByRole('combobox', { name: 'Runtime: sort or filter' })).toBeVisible();
  await page.getByRole('combobox', { name: 'Latest round: sort or filter' }).selectOption('filter:no_rounds');
  await expect(page.getByRole('combobox', { name: 'Latest round: sort or filter' })).toHaveValue('filter:no_rounds');
  await page.locator('#productSearch').fill('');
  await expect(page.locator('#productRows')).toContainText('No rounds fixture');
});

test('B settings wraps Tab and synchronizes switch language', async ({ page, center }) => {
  await openCenter(page, center); await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsForm [type=submit]')).toBeEnabled();
  await page.locator('#settingsForm [type=submit]').focus(); await page.keyboard.press('Tab');
  await expect(page.locator('#settingsForm .dialog-header .dialog-close')).toBeFocused();
  await page.locator('#settingsForm [name=language]').selectOption('zh-CN');
  await page.locator('#settingsForm [type=submit]').click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN');
  await page.locator('#settingsButton').click();
  await expect(page.getByRole('switch', { name: '自动刷新', exact: true })).toBeVisible();
});

test('B import title and close remain visible on a short viewport', async ({ page, center }, info) => {
  await page.setViewportSize({ width: 390, height: 320 });
  await openCenter(page, center); await page.locator('#importButton').click();
  await page.locator('#importForm [name=root]').fill('C:\\A long directory\\Project');
  await page.locator('#probeButton').focus();
  await expect(page.locator('#importForm .dialog-header .dialog-close')).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath('short-import.png') });
});

test('B failed preparation restores only remaining grouped work and stays queued', async ({ page, center }, info) => {
  const operation = { operationId: 'op-failed', revision: 2, kind: 'exploration', state: 'failed', reason: 'fixture failure', batchId: 'batch', canRetry: true, canCancel: true };
  await page.route('**/api/center/v1/operations', route => route.fulfill({ json: envelope({ items: [operation] }) }));
  await page.route('**/api/center/v1/operations/op-failed/restore-draft', route => route.fulfill({ json: envelope({ draft: { groups: [
    { count: 2, direction: 'Original A', config: { engine: 'codex', model: 'model-a', effort: 'high', productLanguage: 'en' } },
    { count: 1, direction: 'Original B', config: { engine: 'codex', model: 'model-b', effort: 'high', productLanguage: 'zh-CN' } }
  ], executionMode: 'enqueue' }, completedCount: 1 }) }));
  await openCenter(page, center); await page.locator('#queueNavButton').click();
  await page.getByRole('button', { name: 'Restore configuration', exact: true }).click();
  await expect(page.locator('#newWorkDialog')).toBeVisible();
  await expect(page.locator('.work-group')).toHaveCount(2);
  await expect(page.locator('.work-group').first().locator('[name=direction]')).toHaveValue('Original A');
  await expect(page.locator('.work-group').first().locator('[name=count]')).toHaveValue('2');
  await expect(page.locator('#newWorkForm input[value=enqueue][data-ui-field]')).toBeChecked();
  await page.screenshot({ path: info.outputPath('restored-groups.png') });
});

test('B a successful write waits for a fresh read after an older refresh', async ({ page, center }) => {
  await openCenter(page, center); await page.locator('#queueNavButton').click();
  let currentCapacity = 4, delayed, reads = 0;
  await page.route('**/api/center/v1/summary', async route => {
    reads++; const payload = await (await route.fetch()).json(); payload.data.maxConcurrentProjects = currentCapacity;
    if (reads === 1) delayed = () => route.fulfill({ json: payload }); else await route.fulfill({ json: payload });
  });
  await page.route('**/api/center/v1/queue/capacity', route => { currentCapacity = route.request().postDataJSON().maxConcurrentProjects; return route.fulfill({ json: envelope({}) }); });
  await page.locator('#capacityForm [name=capacity]').fill('8');
  await expect.poll(() => Boolean(delayed), { timeout: 10000 }).toBe(true);
  await page.locator('#capacityForm [type=submit]').click();
  await expect.poll(() => currentCapacity).toBe(8); await delayed();
  await expect.poll(() => reads).toBeGreaterThanOrEqual(2);
  await expect(page.locator('#capacityForm [name=capacity]')).toHaveValue('8');
});

async function queueFixture(page, center, attention) {
  const entry = { entryId: center.entryId, sourceId: center.sourceId, kind: 'product', displayName: 'Queue fixture',
    revision: 1, sourceRevision: 1, availability: 'available', capabilities: { execute: true }, executionSummary: { state: 'ended' } };
  const request = { requestId: 'request_fixture', entryId: center.entryId, revision: 1, displayName: entry.displayName,
    state: attention ? 'attention' : 'queued', ...(attention ? { dispatchId: 'dispatch_fixture', attentionReason: 'recovery_required' } : {}) };
  const send = (route, data) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ schemaVersion: 1, centerId: 'fixture', revision: 1, observedAt: new Date().toISOString(), data }) });
  await page.route('**/api/center/v1/summary', route => send(route, { language: 'en', dispatchEnabled: false, queueRevision: 1,
    executionAvailable: true, currentRequest: attention ? request : null, queuedCount: attention ? 0 : 1, attentionCount: attention ? 1 : 0 }));
  await page.route('**/api/center/v1/entries?*', route => send(route, { items: [entry], total: 1, nextCursor: null }));
  await page.route('**/api/center/v1/requests?*', route => send(route, { items: [request], revision: 1 }));
  await openCenter(page, center);
  return { entry, request };
}


test('B nested cancellation exposes its message and both distinct actions', async ({ page, center }) => {
  await queueFixture(page, center, false); await page.locator('#queueNavButton').click();
  await page.locator('#queueContent button').filter({ hasText: /^Cancel$/ }).click();
  await expect(page.getByRole('alertdialog').getByRole('button', { name: 'Back', exact: true })).toBeVisible();
  await expect(page.getByRole('alertdialog').getByRole('button', { name: 'Confirm cancellation', exact: true })).toBeVisible();
  expect(await page.locator('#confirmMessage').evaluate(node => Boolean(node.closest('[aria-hidden="true"]')))).toBe(false);
});


test('B recovery confirmation uses reviewed revisions and requires both acknowledgements', async ({ page, center }) => {
  await queueFixture(page, center, true);
  const source = { sourceId: 'source-a', kind: 'runtime', revision: 1, sourceRevision: 2, displayName: 'Recovery fixture', availability: 'available' };
  await page.route(`**/api/center/v1/entries/${center.entryId}`, route => route.fulfill({ json: envelope({ entryId: center.entryId, sourceId: source.sourceId, sources: [source], revision: 1,
    capabilities: { reviewRecovery: true }, recovery: { canReview: true } }) }));
  await page.route('**/api/center/v1/sources/source-a/review-recovery', route => route.fulfill({ json: envelope({ canConfirm: true, reviewToken: 'reviewed', expectedRevision: 3, expectedSourceRevision: 4, checks: [], reasons: [] }) }));
  let submitted;
  await page.route('**/api/center/v1/sources/source-a/confirm-recovery', route => { submitted = route.request().postDataJSON(); return route.fulfill({ json: envelope({ resumed: false }) }); });
  await page.locator('.more-button').first().click(); await page.getByRole('menuitem', { name: 'Manage sources', exact: true }).click();
  await page.locator('#sourceManagerBody button').filter({ hasText: /^Review recovery$/ }).click();
  const confirm = page.locator('.recovery-review').getByRole('button', { name: 'Confirm record recovery', exact: true });
  await expect(confirm).toBeDisabled();
  await page.locator('.recovery-review [role=checkbox]').nth(0).check(); await expect(confirm).toBeDisabled();
  await page.locator('.recovery-review [role=checkbox]').nth(1).check(); await expect(confirm).toBeEnabled();
  await confirm.click(); await expect.poll(() => submitted).toBeTruthy();
  expect(submitted).toMatchObject({ expectedRevision: 3, expectedSourceRevision: 4, reviewToken: 'reviewed', confirmCodeEffects: true, confirmExternalEffects: true });
});

test('B runtime menu in a product opens the environment on the cached center', async ({ page, center }) => {
  await openCenter(page, center); await page.locator('.product-link').first().click();
  await expect(page.locator('#projectName')).toBeVisible();
  await page.locator('#profileButton').click(); await page.getByRole('menuitem', { name: 'Runtime environment', exact: true }).click();
  await expect(page.locator('#environmentDialog')).toBeVisible();
  await expect(page.locator('#environmentForm [name=candidate]')).toBeVisible();
});

test('B template version reload preserves configuration and name', async ({ page, center }) => {
  await openCenter(page, center); await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsForm [type=submit]')).toBeEnabled();
  await page.locator('#settingsForm [name=model]').fill('unsaved-model');
  await page.locator('#settingsForm .template-editor summary, #settingsForm .template-editor .disclosure-trigger').click();
  await page.locator('#settingsForm .template-name').fill('Unsaved template');
  await page.route('**/api/center/v1/templates', route => route.fulfill({ status: 409, json: { code: 'REVISION_CONFLICT' } }));
  await page.locator('#settingsForm').getByRole('button', { name: 'Save template', exact: true }).click();
  await page.getByRole('button', { name: 'Reload templates', exact: true }).click();
  await expect(page.locator('#settingsForm .template-status')).toContainText('preserved');
  await expect(page.locator('#settingsForm [name=model]')).toHaveValue('unsaved-model');
  await expect(page.locator('#settingsForm .template-name')).toHaveValue('Unsaved template');
});
