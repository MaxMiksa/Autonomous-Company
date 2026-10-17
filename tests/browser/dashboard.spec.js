import { test, expect } from './fixtures.js';

async function openCenter(page, center) {
  await page.goto(`${center.url}/center`);
  await expect(page.locator('#observedAt')).not.toBeEmpty();
}

async function refreshRecords(page) {
  await page.locator('#settingsButton').click();
  await page.locator('#refreshButton').click();
  await page.locator('#closeSettingsButton').click();
}

test('old standalone pages resolve to the center and global APIs stay removed', async ({ page, center }) => {
  for (const route of ['/', '/journal', '/journal/', '/legacy', '/legacy/']) {
    await page.goto(`${center.url}${route}`);
    await expect(page).toHaveURL(`${center.url}${route === '/' ? '/' : '/center'}`);
    await expect(page.locator('#productRows')).not.toBeEmpty();
  }
  for (const route of ['/api/journal', '/api/journal/log?id=runtime', '/api/language', '/api/status', '/api/log-tail?lines=180', '/api/consensus']) {
    expect((await page.request.get(`${center.url}${route}`)).status()).toBe(404);
  }
  expect((await page.request.post(`${center.url}/api/action/start`, { data: {} })).status()).toBe(404);
});

test('center language preferences persist and apply to product details', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#settingsButton').click();
  await page.locator('#settingsForm [name="language"]').selectOption('zh-CN');
  await page.locator('#settingsForm [name="productLanguage"]').selectOption('en');
  await page.locator('#settingsForm [type="submit"]').click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN');
  const preferences = (await (await page.request.get(`${center.url}/api/center/v1/preferences`)).json()).data;
  expect(preferences).toMatchObject({ language: 'zh-CN', productLanguage: 'en' });
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN');
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#tab-work')).toHaveText('工作记录');
  await expect(page.locator('#runtimeActionButton, #runtimeControls, #languageSelect')).toHaveCount(0);
  await expect(page.locator('#journalBackLink')).toHaveJSProperty('href', `${center.url}/center`);
});

test('failed center language save stays visible and does not claim success', async ({ page, center }) => {
  await openCenter(page, center);
  await page.route('**/api/center/v1/preferences', route => route.request().method() === 'POST'
    ? route.fulfill({ status: 503, json: { code: 'CENTER_UNAVAILABLE', message: 'Fixture save unavailable' } })
    : route.continue());
  await page.locator('#settingsButton').click();
  await page.locator('#settingsForm [name="language"]').selectOption('zh-CN');
  await page.locator('#settingsForm [name="productLanguage"]').selectOption('en');
  await page.locator('#settingsForm [type="submit"]').click();
  await expect(page.locator('#settingsDialog')).toContainText('Fixture save unavailable');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  expect((await (await page.request.get(`${center.url}/api/center/v1/preferences`)).json()).data.language).toBe('en');
});

for (const view of ['center', 'detail']) {
  test(`${view} settings expose four working documentation links`, async ({ page, center }) => {
    await page.goto(`${center.url}/${view === 'center' ? 'center' : `products/${center.entryId}`}`);
    await page.locator('#settingsButton').click();
    for (const name of ['readme', 'setup', 'troubleshooting', 'language']) {
      const link = page.locator(`#settingsDialog a[href="/docs/${name}"]`);
      await expect(link).toBeVisible();
      await expect(link).toHaveAttribute('target', '_blank');
      const response = await page.request.get(`${center.url}/docs/${name}`);
      expect(response.ok()).toBeTruthy();
      expect((await response.text()).length).toBeGreaterThan(200);
    }
    await expect(page.locator('#settingsDialog a[href*="consensus"]')).toHaveCount(0);
  });
}

test('detail refresh failure retains records and recovers through visible settings', async ({ page, center }) => {
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#cycleNumber')).toHaveText('06');
  const route = '**/api/center/v1/entries/*/journal?*';
  await page.route(route, route => route.fulfill({ status: 503, json: { code: 'CENTER_UNAVAILABLE', message: 'Fixture read unavailable' } }));
  await refreshRecords(page);
  await expect(page.locator('#connectionError')).toBeVisible();
  await expect(page.locator('#cycleNumber')).toHaveText('06');
  await page.unroute(route);
  await refreshRecords(page);
  await expect(page.locator('#connectionError')).toBeHidden();
});

test('unavailable detail bootstrap remains navigable and recovers through visible settings', async ({ page, center }) => {
  const route = '**/api/center/v1/entries/*/journal?*';
  await page.route(route, route => route.fulfill({ status: 503, json: { code: 'CENTER_UNAVAILABLE' } }));
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#connectionError')).toBeVisible();
  await expect(page.locator('#journalBackLink')).toBeVisible();
  await page.locator('#settingsButton').click();
  await expect(page.locator('#refreshButton')).toBeEnabled();
  await page.locator('#closeSettingsButton').click();
  await page.unroute(route);
  await refreshRecords(page);
  await expect(page.locator('#cycleNumber')).toHaveText('06');
  await expect(page.locator('#connectionError')).toBeHidden();
});
