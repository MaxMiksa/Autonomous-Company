import { test as base, expect } from '@playwright/test';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';

const test = base.extend({
  centerCycles: [6, { option: true }],
  centerExplorationCycles: [0, { option: true }],
  center: async ({ centerCycles, centerExplorationCycles }, use, testInfo) => {
    const child = spawn(process.env.AUTONOMOUS_COMPANY_BROWSER_PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
      ['-u', fileURLToPath(new URL('center-fixture-server.py', import.meta.url)), '--cycles', String(centerCycles), '--exploration-cycles', String(centerExplorationCycles)],
      { stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true });
    let output = '';
    child.stderr.on('data', chunk => { output += chunk; });
    const closed = new Promise(resolve => child.once('close', resolve));
    const lines = createInterface({ input: child.stdout });
    try {
      const center = await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error(`Center fixture timed out: ${output}`)), 15000);
        const finish = (error, value) => { clearTimeout(timer); error ? reject(error) : resolve(value); };
        child.once('error', error => finish(error));
        child.once('exit', code => finish(new Error(`Center fixture exited ${code}: ${output}`)));
        lines.once('line', line => { try { finish(null, JSON.parse(line)); } catch (error) { finish(error); } });
      });
      await use(center);
    } finally {
      child.stdin.end();
      let timer;
      await Promise.race([closed, new Promise(resolve => { timer = setTimeout(() => { child.kill(); resolve(); }, 5000); })]);
      clearTimeout(timer);
      lines.close();
      if (testInfo.status !== testInfo.expectedStatus) await testInfo.attach('center-server.log', { body: output, contentType: 'text/plain' });
    }
  },
  page: async ({ page }, use) => {
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await use(page);
    expect(errors).toEqual([]);
  },
});

async function openCenter(page, center) {
  await page.goto(`${center.url}/center`);
  await expect(page.locator('#observedAt')).not.toBeEmpty();
}

for (const kind of ['center', 'journal']) {
  test(`${kind} first paint stays styled while UI scripts are delayed`, async ({ page, center }) => {
    let release;
    const pending = new Promise(resolve => { release = resolve; });
    await page.route('**/ui-assets/ui.js', async route => { await pending; await route.continue(); });
    try {
      await page.goto(`${center.url}/${kind === 'center' ? 'center' : `products/${center.entryId}`}`, { waitUntil: 'commit' });
      const header = page.locator(kind === 'center' ? '.center-header' : '.site-header');
      await expect(header).toBeVisible();
      // Wait for stylesheet application while the component bundle remains blocked.
      await expect.poll(() => page.locator('.brand-logo').evaluate(node => node.complete && node.naturalWidth > 0 ? node.getBoundingClientRect().height : 0)).toBeCloseTo(44.16, 1);
      const before = await page.evaluate(() => {
        window.initialFrame = document.querySelector('.app-frame');
        window.initialView = document.querySelector('.workspace-view');
        return {
          booted: Boolean(window.createDashboardUI),
          skipBottom: document.querySelector('.skip-link').getBoundingClientRect().bottom,
          header: document.querySelector('header').getBoundingClientRect().toJSON(),
        };
      });
      expect(before.booted).toBe(false);
      expect(before.skipBottom).toBeLessThanOrEqual(0);
      expect(before.header.height).toBe(56);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      release();
      await page.waitForLoadState('load');
      await expect.poll(() => page.evaluate(() => window.DashboardNavigation.inspect().active)).toBe(kind);
      const after = await page.evaluate(() => ({
        sameFrame: window.initialFrame === document.querySelector('.app-frame'),
        sameView: window.initialView === document.querySelector('.workspace-view'),
        header: document.querySelector('header').getBoundingClientRect().toJSON(),
      }));
      expect(after.sameFrame).toBe(true);
      expect(after.sameView).toBe(true);
      await expect(page.locator('.app-frame')).toHaveCount(1);
      await expect(page.locator('.workspace-view')).toHaveCount(1);
      for (const key of ['x', 'y', 'width', 'height']) expect(after.header[key]).toBeCloseTo(before.header[key], 1);
    } finally { release(); }
  });
}

test('search icon stays fixed throughout expansion and collapse', async ({ page, center }) => {
  await openCenter(page, center);
  for (const width of [1359, 390]) {
    await page.setViewportSize({ width, height: 919 });
    await page.mouse.move(0, 0);
    await page.waitForTimeout(220);
    const result = await page.evaluate(async () => {
      const input = document.querySelector('#productSearch'), icon = document.querySelector('.search-field svg');
      const samples = [icon.getBoundingClientRect().toJSON()];
      for (const expanded of [true, false]) {
        expanded ? input.focus() : input.blur();
        const start = performance.now();
        while (performance.now() - start < 230) {
          await new Promise(requestAnimationFrame); samples.push(icon.getBoundingClientRect().toJSON());
        }
      }
      return samples;
    });
    for (const sample of result) for (const key of ['x', 'y']) expect(Math.abs(sample[key] - result[0][key])).toBeLessThan(0.2);
  }
});

test('settings exit holds its horizontal position and reverses the entrance offset', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#settingsButton').click();
  await expect.poll(() => page.locator('.ac-dialog').evaluate(node => getComputedStyle(node).opacity)).toBe('1');
  const result = await page.evaluate(() => {
    const node = document.querySelector('#settingsDialog').parentElement;
    const before = node.getBoundingClientRect().toJSON();
    document.querySelector('#settingsDialog').close();
    const exit = document.querySelector('[data-motion-exit]'), animations = exit.getAnimations();
    animations.forEach(animation => animation.pause());
    const samples = [0, 90, 180].map(time => {
      animations.forEach(animation => { animation.currentTime = time; });
      return { ...exit.getBoundingClientRect().toJSON(), opacity: Number(getComputedStyle(exit).opacity) };
    });
    animations.forEach(animation => animation.play());
    return { before, samples };
  });
  for (const sample of result.samples) {
    expect(sample.x).toBeCloseTo(result.before.x, 1);
    expect(sample.width).toBeCloseTo(result.before.width, 1);
    expect(sample.height).toBeCloseTo(result.before.height, 1);
  }
  expect(result.samples[0].y).toBeCloseTo(result.before.y, 1);
  expect(result.samples[2].y - result.before.y).toBeCloseTo(6, 1);
  expect(result.samples[1].opacity).toBeGreaterThan(0);
  expect(result.samples[1].opacity).toBeLessThan(1);
});

test('settings motion preserves draft, position and focus across rapid reversals', async ({ page, center }, testInfo) => {
  await openCenter(page, center);
  await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsForm .form-status')).toHaveText('');
  await page.locator('#settingsForm [name=model]').fill('unsaved-motion-draft');
  const samples = await page.evaluate(() => {
    const form = document.querySelector('#settingsForm'), results = [];
    for (let index = 0; index < 12; index++) {
      const live = document.querySelector('#settingsDialog').parentElement;
      live.getAnimations().forEach(animation => { animation.pause(); animation.currentTime = 70; });
      const beforeClose = live.getBoundingClientRect().toJSON();
      document.querySelector('#settingsDialog').close();
      const exit = document.querySelector('[data-motion-exit]');
      const afterClose = exit.getBoundingClientRect().toJSON();
      exit.getAnimations().forEach(animation => { animation.pause(); animation.currentTime = 60; });
      const beforeOpen = exit.getBoundingClientRect().toJSON();
      document.querySelector('#settingsButton').click();
      const reopened = document.querySelector('#settingsDialog').parentElement;
      results.push({ beforeClose, afterClose, beforeOpen, afterOpen: reopened.getBoundingClientRect().toJSON(), sameForm: form === document.querySelector('#settingsForm') });
    }
    return results;
  });
  await testInfo.attach('settings-motion-reversals.json', { body: JSON.stringify(samples, null, 2), contentType: 'application/json' });
  for (const sample of samples) {
    expect(sample.sameForm).toBe(true);
    for (const key of ['x', 'y', 'width', 'height']) {
      expect(Math.abs(sample.beforeClose[key] - sample.afterClose[key])).toBeLessThan(1);
      expect(Math.abs(sample.beforeOpen[key] - sample.afterOpen[key])).toBeLessThan(1);
    }
  }
  await page.waitForTimeout(260);
  await expect(page.locator('#settingsForm [name=model]')).toHaveValue('unsaved-motion-draft');
  await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
  await expect(page.locator('.ac-dialog')).toHaveCount(1);
  await page.keyboard.press('Escape');
  await expect(page.locator('#settingsButton')).toBeFocused();
  await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
  expect(await page.evaluate(() => document.body.style.pointerEvents)).not.toBe('none');
});

test('local motion settles safely on resize, reduced motion and backgrounding', async ({ page, center }) => {
  await openCenter(page, center);
  for (const event of ['resize', 'reduced', 'hidden', 'missing']) {
    await page.locator('#settingsButton').click();
    await expect(page.locator('#settingsForm .form-status')).toHaveText('');
    await page.evaluate(() => document.querySelector('#settingsDialog').close());
    if (event === 'resize') await page.setViewportSize({ width: 390, height: 844 });
    if (event === 'reduced') await page.emulateMedia({ reducedMotion: 'reduce' });
    if (event === 'hidden') await page.evaluate(() => {
      Object.defineProperty(document, 'hidden', { configurable: true, value: true });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
    await expect(page.locator('#settingsButton')).toBeFocused();
    if (event === 'reduced') await page.emulateMedia({ reducedMotion: 'no-preference' });
    if (event === 'hidden') await page.evaluate(() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); });
    if (event === 'missing') {
      await page.evaluate(() => { Element.prototype.animate = undefined; });
      await page.locator('#settingsButton').click();
      await expect(page.locator('#settingsForm')).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
    }
  }
  expect(await page.evaluate(() => document.body.style.pointerEvents)).not.toBe('none');
});

test('detail return starts promptly on both the header and page timelines', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('.product-link').first().click();
  await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
  const result = await page.evaluate(async () => {
    const navigation = document.querySelector('.topbar > .navline');
    const main = document.querySelector('#mainContent');
    document.querySelector('#journalBackLink').click();
    const animation = navigation.getAnimations()[0];
    if (!animation) return null;
    await animation.ready;
    const rate = animation.playbackRate;
    animation.pause();
    const duration = Number(animation.effect.getTiming().duration);
    const opacity = [0, duration / 3, duration].map(time => { animation.currentTime = time; return Number(getComputedStyle(navigation).opacity); });
    const bodyAnimation = main.getAnimations()[0];
    bodyAnimation.pause(); bodyAnimation.currentTime = 100;
    const bodyOpacity = Number(getComputedStyle(main).opacity);
    const bodyDuration = Number(bodyAnimation.effect.getTiming().duration);
    const surface = document.querySelector('.workspace-motion-surface');
    const surfaceAnimation = surface.getAnimations()[0];
    surfaceAnimation.pause(); surfaceAnimation.currentTime = 100;
    const surfaceOpacity = Number(getComputedStyle(surface).opacity);
    const coveringBackground = getComputedStyle(main.closest('.workspace-view')).backgroundColor;
    const centerVisible = !document.querySelector('[data-view=center]').hidden;
    surfaceAnimation.play();
    bodyAnimation.play();
    animation.play();
    return { rate, opacity, bodyOpacity, bodyDuration, surfaceOpacity, coveringBackground, centerVisible };
  });
  expect(result).not.toBeNull();
  expect(result.rate).toBe(1);
  expect(result.opacity[0]).toBe(1);
  expect(result.opacity[1]).toBeGreaterThan(0);
  expect(result.opacity[1]).toBeLessThan(0.5);
  expect(result.opacity[2]).toBe(0);
  expect(result.bodyDuration).toBe(300);
  expect(result.bodyOpacity).toBeGreaterThan(0);
  expect(result.bodyOpacity).toBeLessThan(0.5);
  expect(result.surfaceOpacity).toBeCloseTo(result.bodyOpacity, 4);
  expect(result.coveringBackground).toBe('rgba(0, 0, 0, 0)');
  expect(result.centerVisible).toBe(true);
  await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
  await expect(page.locator('[data-workspace-motion]')).toHaveCount(0);
});

test('detail header keeps its width through a delayed response and places the read-only icon beside the title', async ({ page, center }, testInfo) => {
  for (const width of [1359, 390]) {
    await page.setViewportSize({ width, height: 919 });
    await openCenter(page, center);
    let release;
    const pending = new Promise(resolve => { release = resolve; });
    const routePattern = '**/journal?*';
    await page.route(routePattern, async route => { await pending; await route.continue(); });
    const snapshot = () => page.evaluate(() => Object.fromEntries(['.topbar > .navline', '.topbar .ac-tabs-host', '.workspace-project-heading'].map(selector => {
      const box = document.querySelector(selector).getBoundingClientRect();
      return [selector, { x: box.x, width: box.width }];
    })));
    try {
      await page.locator('.product-link').first().click();
      await expect(page.locator('#journalBackLink')).toBeVisible();
      const before = await snapshot();
      release();
      await expect(page.locator('#cycleTitle')).toBeVisible();
      await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
      const after = await snapshot();
      await testInfo.attach(`stable-header-${width}.json`, { body: JSON.stringify({ before, after }, null, 2), contentType: 'application/json' });
      for (const selector of Object.keys(before)) for (const key of ['x', 'width']) expect(after[selector][key]).toBeCloseTo(before[selector][key], 1);
      await expect(page.locator('.workspace-project-heading #readOnlyIndicator')).toBeVisible();
      await expect(page.locator('#readOnlyIndicator')).toHaveAttribute('aria-label', /Read.only|只读/i);
      const icon = await page.locator('#readOnlyIndicator').boundingBox();
      const name = await page.locator('#workspaceProjectName').boundingBox();
      expect(icon.x - name.x - name.width).toBeCloseTo(4, 1);
      expect(await page.locator('#runtimeState').evaluate(node => node.classList.contains('sr-only'))).toBe(true);
      await expect(page.locator('#runtimeControls')).toBeHidden();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    } finally { release(); await page.unroute(routePattern); }
  }
});

test('fluid navigation reveals its rounded shape and name together without a flying label', async ({ page, center }, testInfo) => {
  await openCenter(page, center);
  for (const width of [1359, 390]) {
    await page.setViewportSize({ width, height: 919 });
    await page.locator('.product-link').first().click();
    await expect(page.locator('#cycleTitle')).toBeVisible();
    await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
    await page.locator('#journalBackLink').click();
    await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
    const result = await page.evaluate(async () => {
      document.querySelector('.product-link').click();
      const navigation = document.querySelector('.topbar > .navline');
      const path = navigation.querySelector('.navigation-fluid-surface path');
      const label = document.querySelector('#workspaceProjectName');
      const animations = document.getAnimations();
      await Promise.all(animations.map(animation => animation.ready));
      animations.forEach(animation => animation.pause());
      const duration = Math.max(...animations.map(animation => Number(animation.effect.getTiming().duration)));
      const snapshot = () => ({ path: getComputedStyle(path).d, shape: path.getBBox().toJSON ? path.getBBox().toJSON() : { y: path.getBBox().y, height: path.getBBox().height }, label: label.getBoundingClientRect().toJSON(), opacity: Number(getComputedStyle(label.closest('.workspace-project-heading')).opacity), navigation: navigation.getBoundingClientRect().toJSON() });
      const frames = [0, duration / 3, duration].map(time => { animations.forEach(animation => { animation.currentTime = time; }); return snapshot(); });
      animations.forEach(animation => { animation.currentTime = duration / 3; });
      const before = snapshot();
      document.querySelector('#journalBackLink').click();
      const after = snapshot();
      const flyingLabels = document.querySelectorAll('.workspace-motion-identity').length;
      animations.forEach(animation => animation.play());
      return { frames, before, after, flyingLabels };
    });
    await testInfo.attach(`fluid-navigation-${width}.json`, { body: JSON.stringify(result, null, 2), contentType: 'application/json' });
    expect(result.flyingLabels).toBe(0);
    expect(result.frames[0].shape.height).toBe(0);
    expect(result.frames[1].shape.height).toBeGreaterThan(0);
    expect(result.frames[1].shape.height).toBeLessThan(result.frames[2].shape.height);
    expect(result.frames[2].shape.height).toBeCloseTo(result.frames[2].navigation.height, 1);
    expect(result.frames[0].opacity).toBe(0); expect(result.frames[2].opacity).toBe(1);
    for (const frame of result.frames) expect(frame.label.x).toBeCloseTo(result.frames[2].label.x, 1);
    expect(result.after.path).toBe(result.before.path);
    expect(result.after.label.y).toBeCloseTo(result.before.label.y, 1);
    await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
    await expect(page.locator('.navigation-fluid-surface')).toHaveCount(0);
    await expect(page.locator('.product-link').first()).toBeFocused();
  }
});

test('fluid navigation can reopen during exit without losing the detail view', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('.product-link').first().click();
  await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
  const result = await page.evaluate(async () => {
    const navigation = document.querySelector('.topbar > .navline');
    document.querySelector('#journalBackLink').click();
    await new Promise(resolve => setTimeout(resolve, 90));
    const path = navigation.querySelector('.navigation-fluid-surface path');
    const before = getComputedStyle(path).d;
    document.querySelector('.product-link').click();
    return { before, after: getComputedStyle(path).d };
  });
  expect(result.after).toBe(result.before);
  await expect.poll(() => page.evaluate(() => DashboardNavigation.inspect().transitioning)).toBe(false);
  await expect(page.locator('#cycleTitle')).toBeVisible();
  await expect(page.locator('.navigation-fluid-surface')).toHaveCount(0);
  await expect(page.locator('.workspace-motion-identity')).toHaveCount(0);
  await expect(page.locator('#workspaceProjectName')).toBeVisible();
  await page.locator('#journalBackLink').click();
  await expect(page.locator('.product-link').first()).toBeFocused();
});

test('motion gate: reversing entry uses the current frame and restores the real row', async ({ page, center }, testInfo) => {
  await openCenter(page, center);
  const result = await page.evaluate(async () => {
    const link = document.querySelector('.product-link');
    const shell = document.querySelector('.app-frame');
    link.click();
    const frames = [];
    let reversed = false, before, after;
    await new Promise((resolve, reject) => {
      const started = performance.now();
      function sample() {
        const surface = document.querySelector('.workspace-motion-surface');
        if (surface) {
          const animation = surface.getAnimations()[0];
          const rect = surface.getBoundingClientRect();
          frames.push({ time: performance.now(), progress: animation?.currentTime, x: rect.x, y: rect.y, width: rect.width, height: rect.height,
            background: getComputedStyle(surface).backgroundColor, pageBackground: getComputedStyle(shell).backgroundColor, borderWidth: getComputedStyle(surface).borderTopWidth });
          if (!reversed && animation?.currentTime >= 70) {
            before = rect.toJSON();
            document.querySelector('#journalBackLink').click();
            after = surface.getBoundingClientRect().toJSON(); reversed = true;
          }
        } else if (reversed) { resolve(); return; }
        if (performance.now() - started > 5000) { reject(new Error('Navigation did not reverse')); return; }
        requestAnimationFrame(sample);
      }
      requestAnimationFrame(sample);
    });
    return { before, after, frames, sameShell: shell === document.querySelector('.app-frame'), activeKey: document.activeElement.dataset.focusKey, href: location.pathname };
  });
  await testInfo.attach('navigation-reversal-frames.json', { body: JSON.stringify(result, null, 2), contentType: 'application/json' });
  expect(result.sameShell).toBe(true);
  expect(result.href).toBe('/center');
  for (const key of ['x', 'y', 'width', 'height']) expect(Math.abs(result.after[key] - result.before[key])).toBeLessThan(0.1);
  expect(result.frames.length).toBeGreaterThan(3);
  for (const frame of result.frames) {
    expect(frame.background).toBe(frame.pageBackground);
    expect(frame.borderWidth).toBe('0px');
  }
  expect(result.frames.at(-1).height).toBeLessThan(result.before.height);
  await expect(page.locator('.product-link').first()).toBeFocused();
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await expect(page.locator('#productSearch')).toBeVisible();
});

test('workspace lifecycle stays bounded through twenty visits and browser history', async ({ page, center }, testInfo) => {
  test.setTimeout(60000);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.addInitScript(() => {
    const set = window.setInterval, clear = window.clearInterval;
    window.activeIntervals = new Set();
    window.setInterval = (...args) => { const id = set(...args); window.activeIntervals.add(id); return id; };
    window.clearInterval = id => { window.activeIntervals.delete(id); clear(id); };
  });
  await openCenter(page, center);
  const cdp = await page.context().newCDPSession(page);
  const samples = [];
  for (let index = 0; index < 20; index++) {
    await page.locator('.product-link').first().click();
    await expect(page.locator('#cycleTitle')).toBeVisible();
    await page.locator('#journalBackLink').click();
    await expect(page.locator('.product-link').first()).toBeFocused();
    expect(await page.evaluate(() => window.activeIntervals.size)).toBe(1);
    expect(await page.locator('.workspace-view').count()).toBe(1);
    await cdp.send('HeapProfiler.collectGarbage');
    samples.push(await cdp.send('Memory.getDOMCounters'));
  }
  await testInfo.attach('lifecycle-counters.json', { body: JSON.stringify(samples, null, 2), contentType: 'application/json' });
  expect(samples.at(-1).documents).toBeLessThanOrEqual(samples[2].documents + 1);
  expect(samples.at(-1).nodes).toBeLessThan(samples[2].nodes + 100);
  expect(samples.at(-1).jsEventListeners).toBeLessThan(samples[2].jsEventListeners + 10);
  await page.goBack(); await expect(page.locator('#cycleTitle')).toBeVisible();
  await page.goForward(); await expect(page.locator('.product-link').first()).toBeVisible();
});

test('return while a detail template is loading ignores its late completion', async ({ page, center }) => {
  await openCenter(page, center);
  let release;
  await page.route('**/products/*', async route => {
    await new Promise(resolve => { release = resolve; });
    await route.continue();
  });
  await page.locator('.product-link').first().click();
  await expect.poll(() => Boolean(release)).toBe(true);
  await page.goBack();
  await expect(page.locator('.product-link').first()).toBeFocused();
  release();
  await page.waitForTimeout(400);
  await expect(page).toHaveURL(`${center.url}/center`);
  await expect(page.locator('#mainContent')).toHaveCount(0);
  await expect(page.locator('#productSearch')).toBeEnabled();
});

test('closing dialogs can reopen from their visible position without losing the form', async ({ page, center }, testInfo) => {
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  await page.locator('[name=direction]').fill('Keep this unfinished draft');
  const result = await page.evaluate(async () => {
    const form = document.querySelector('#newWorkForm');
    document.querySelector('#newWorkDialog').close();
    await new Promise(resolve => setTimeout(resolve, 50));
    const before = document.querySelector('[data-motion-exit]').getBoundingClientRect().toJSON();
    const beforeTransform = getComputedStyle(document.querySelector('[data-motion-exit]')).transform;
    document.querySelector('#newWorkButton').click();
    const after = document.querySelector('#newWorkDialog').parentElement.getBoundingClientRect().toJSON();
    const surface = document.querySelector('#newWorkDialog').parentElement;
    return { before, after, beforeTransform, afterTransform: getComputedStyle(surface).transform, animations: surface.getAnimations().map(a => ({ time: a.currentTime, frames: a.effect.getKeyframes() })), style: surface.getAttribute('style'), same: form === document.querySelector('#newWorkForm') };
  });
  await testInfo.attach('dialog-reversal.json', { body: JSON.stringify(result), contentType: 'application/json' });
  await writeFile(testInfo.outputPath('dialog-reversal.json'), JSON.stringify(result, null, 2));
  expect(result.same).toBe(true);
  for (const key of ['x', 'y', 'width', 'height']) expect(Math.abs(result.before[key] - result.after[key])).toBeLessThan(1);
  await expect(page.locator('[name=direction]')).toHaveValue('Keep this unfinished draft');
  await page.waitForTimeout(250);
  await expect(page.locator('#newWorkDialog')).toBeVisible();
  await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
  await page.keyboard.press('Escape');
  await expect(page.locator('#newWorkButton')).toBeFocused();
  await expect(page.locator('#newWorkDialog')).not.toBeVisible();
});

test('cycle reversals retain the current height and stable refresh nodes', async ({ page, center }, testInfo) => {
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#cycleTitle')).toBeVisible();
  const result = await page.evaluate(async () => {
    const row = document.querySelector('#historyList .cycle-row');
    const button = row.querySelector('.disclosure-trigger');
    const panel = row.querySelector('[data-slot=collapsible-content]');
    button.click();
    await new Promise(resolve => setTimeout(resolve, 70));
    const before = panel.getBoundingClientRect().height;
    button.click();
    const after = panel.getBoundingClientRect().height;
    return { before, after, inert: panel.inert };
  });
  expect(result.before).toBeGreaterThan(0);
  expect(Math.abs(result.before - result.after)).toBeLessThan(1);
  expect(result.inert).toBe(true);
  await expect(page.locator('#historyList .cycle-row').first().locator('[data-slot=collapsible-content]')).toBeHidden();
  await page.evaluate(() => { window.savedCycleNode = document.querySelector('#currentCycle .cycle-row'); });
  await page.locator('#settingsButton').click();
  await page.locator('#refreshButton').click();
  await page.keyboard.press('Escape');
  expect(await page.evaluate(() => window.savedCycleNode === document.querySelector('#currentCycle .cycle-row'))).toBe(true);
  await testInfo.attach('disclosure-reversal.json', { body: JSON.stringify(result), contentType: 'application/json' });
});

test('late product reads cannot populate a replacement detail, and animation failures preserve navigation', async ({ page, center }) => {
  await openCenter(page, center);
  let release;
  await page.route(`**/entries/${center.entryId}/journal?*`, async route => {
    const response = await route.fetch();
    await new Promise(resolve => { release = resolve; });
    try { await route.fulfill({ response }); } catch { /* The abandoned read may already be aborted. */ }
  });
  await page.locator('.product-link').first().click();
  await expect.poll(() => Boolean(release)).toBe(true);
  await page.evaluate(() => DashboardNavigation.navigate('/products/absent-test-product'));
  await expect(page.locator('#connectionError')).toBeVisible();
  release(); await page.waitForTimeout(100);
  await expect(page).toHaveURL(`${center.url}/products/absent-test-product`);
  await expect(page.locator('#cycleTitle')).toHaveCount(0);
  await page.locator('#journalBackLink').click();
  await page.unroute(`**/entries/${center.entryId}/journal?*`);
  await page.evaluate(() => { Element.prototype.animate = () => { throw new Error('Test animation failure'); }; });
  await page.locator('.product-link').first().click();
  await expect(page.locator('#cycleTitle')).toBeVisible();
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await page.locator('#journalBackLink').click();
  await expect(page.locator('.product-link').first()).toBeFocused();
});

test('other products show four by default and expand with standard keyboard controls', async ({ page, center }) => {
  await page.route('**/api/center/v1/entries?*', async route => {
    const payload = await (await route.fetch()).json(), original = payload.data.items[0];
    payload.data.items = Array.from({ length: 12 }, (_, index) => ({ ...original,
      entryId: `${original.entryId}-${index}`, displayName: `Product ${index + 1}`,
      lastActivityAt: new Date(Date.now() - index * 60000).toISOString(),
      readonlyObservation: { readOnly: true, scoped: true, state: index === 0 ? 'running' : 'ended',
        processState: index === 0 ? 'running' : 'stopped', liveConfirmedAt: new Date().toISOString(), observedAt: new Date().toISOString() } }));
    payload.data.total = 12; payload.data.nextCursor = null;
    await route.fulfill({ json: payload });
  });
  await openCenter(page, center);
  const other = page.locator('.product-group').nth(1);
  await expect(other.locator('.product-row:visible')).toHaveCount(4);
  await expect(other.locator('.product-link:visible')).toHaveText(['Product 5', 'Product 6', 'Product 7', 'Product 8']);
  await expect(page.locator('.status-cell strong').first()).toHaveText('Running');
  const toggle = other.getByRole('button', { name: 'Show all 8', exact: true });
  await toggle.focus(); await page.keyboard.press('Enter');
  await expect(other.locator('.product-row:visible')).toHaveCount(8);
  await expect(other.getByRole('button', { name: 'Show less', exact: true })).toHaveAttribute('aria-expanded', 'true');
  await page.locator('#settingsButton').click();
  await page.locator('#centerRefreshButton').click();
  await page.keyboard.press('Escape');
  await expect(other.locator('.product-row:visible')).toHaveCount(8);
  await other.getByRole('button', { name: 'Show less', exact: true }).click();
  await expect(other.locator('.product-row:visible')).toHaveCount(4);
  await page.locator('[data-filter="running"]').click();
  await expect(page.locator('.product-link:visible')).toHaveText(['Product 1']);
});

test('unconfirmed source status agrees across center and detail while English filters remain visible at 1064px', async ({ page, center }) => {
  await page.setViewportSize({ width: 1064, height: 750 });
  await openCenter(page, center);
  expect(await page.locator('[data-filter="archived"]').evaluate(node => {
    const rect = node.getBoundingClientRect();
    const hit = document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2);
    return node.contains(hit);
  })).toBe(true);
  await expect(page.locator('.status-cell > .status-symbol svg').first()).toHaveAttribute('data-lucide', 'circle-help');
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#projectRuntimeStatus')).toContainText('Status unconfirmed');
  await expect(page.locator('#projectRuntimeStatus svg')).toHaveAttribute('data-lucide', 'circle-help');
  await expect(page.locator('#runtimeEvidence')).not.toBeEmpty();
  await expect(page.locator('#sidebarSlot')).toHaveText('No');
});

test('column controls sort globally, filter states and rounds, preserve focus, and show logo fallback', async ({ page, center }, testInfo) => {
  await page.route('**/api/center/v1/entries?*', async route => {
    const response = await route.fetch(), payload = await response.json(), original = payload.data.items[0];
    const names = ['Zeta', 'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon'];
    const rounds = [6, 1, 5, 2, 4, 3], statuses = ['completed', 'running', 'completed', 'failed', 'not_started', 'startup_unconfirmed'];
    const runtimeStates = ['read_only', 'paused', 'ended', 'queued', 'idle', 'unknown'];
    payload.data.items = names.map((displayName, index) => ({ ...original, displayName, entryId: `${original.entryId}-${index}`, cycleNumber: rounds[index], latestCycleStatus: statuses[index], executionSummary: { state: runtimeStates[index] }, capabilities: { ...original.capabilities, execute: true }, latestWork: index === 0 ? { scope: 'exploration', cycleNumber: 2, isLatestCycle: false } : null, thumbnailUrl: index === 0 ? '/api/center/v1/invalid-preview' : null, iconUrl: null }));
    payload.data.total = names.length; payload.data.nextCursor = null;
    await route.fulfill({ json: payload });
  });
  await openCenter(page, center);
  await expect(page.locator('.product-group').first().locator('.product-row')).toHaveCount(4);
  await expect(page.locator('.thumbnail-missing-label')).toHaveCount(0);
  await expect(page.locator('.thumbnail-missing .product-icon svg')).toHaveCount(6);
  await expect(page.locator('.status-symbol svg')).toHaveCount(12);
  await expect(page.locator('[data-filter="running"] .filter-count')).toHaveCount(0);
  const productSort = page.locator('[data-focus-key="column:primary:name"]');
  await productSort.click();
  await expect(productSort).toBeFocused();
  await expect(page.locator('.product-group').first().locator('.product-link')).toHaveText(['Alpha', 'Beta', 'Delta', 'Epsilon']);
  await expect(page.locator('.product-group').first().locator('h2')).toContainText('Recent products');
  const runtime = page.locator('[data-focus-key="column:primary:status"]');
  await runtime.selectOption('filter:queued');
  await expect(runtime).toBeFocused();
  await expect(page.locator('.product-link')).toHaveText(['Gamma']);
  await expect(page.locator('[data-filter="queued"]')).toHaveAttribute('aria-pressed', 'true');
  await runtime.selectOption('filter:all');
  for (const [status, name] of [['paused', 'Alpha'], ['ended', 'Beta'], ['idle', 'Delta'], ['unknown', 'Epsilon']]) {
    await runtime.selectOption(`filter:${status}`);
    await expect(page.locator('.product-link')).toHaveText(status === 'unknown' ? ['Epsilon', 'Zeta'] : [name]);
    await expect(runtime).toBeFocused();
    await page.reload();
    await expect(runtime).toHaveValue(`filter:${status}`);
    await expect(page.locator('.product-link')).toHaveText(status === 'unknown' ? ['Epsilon', 'Zeta'] : [name]);
    await runtime.selectOption('filter:all');
  }
  await expect(page.locator('.work-source')).toHaveCount(0);
  const round = page.locator('[data-focus-key="column:primary:round"]');
  for (const [status, name, label] of [['not_started', 'Delta', 'Not started'], ['startup_unconfirmed', 'Epsilon', 'Startup unconfirmed']]) {
    await round.selectOption(`filter:${status}`);
    await expect(page.locator('.product-link')).toHaveText([name]);
    await expect(page.locator('.round-label')).toHaveText(label);
    await round.selectOption('filter:all');
  }
  await round.selectOption('filter:completed');
  await expect(page.locator('.product-link')).toHaveText(['Beta', 'Zeta']);
  await round.selectOption('sort:desc');
  await expect(page.locator('.product-link')).toHaveText(['Zeta', 'Beta']);
  await round.selectOption('filter:all');
  await expect(page.locator('.product-group').first().locator('.round-number')).toHaveText(['#06', '#05', '#04', '#03']);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(productSort).toBeVisible();
  await expect(round).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const evidence = testInfo.outputPath('fixtures');
  await mkdir(evidence, { recursive: true });
  await page.screenshot({ path: `${evidence}/center-mobile-columns-fixture.png` });
  await page.setViewportSize({ width: 1064, height: 750 });
  await page.locator('[data-focus-key="column:primary:activity"]').click();
  await page.screenshot({ path: `${evidence}/center-columns-fixture.png` });
});

test('disconnected execution explains the disabled action inline without an info icon', async ({ page, center }) => {
  await page.route('**/api/center/v1/summary', async route => {
    const payload = await (await route.fetch()).json(); payload.data.executionAvailable = false;
    await route.fulfill({ json: payload });
  });
  await openCenter(page, center);
  await expect(page.locator('#newWorkButton')).toBeDisabled();
  await expect(page.locator('#newWorkInfo')).toHaveCount(0);
  await expect(page.locator('#newWorkUnavailable')).toBeVisible();
  await expect(page.locator('#newWorkUnavailable')).toContainText('No managed execution environment');
  expect(await page.locator('#capacitySummary').evaluate(node => !!node.closest('.queue-sidebar'))).toBe(true);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#newWorkUnavailable')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('center and long form obey every layout breakpoint, touch targets and enlarged text', async ({ page, center, browser }, testInfo) => {
  await openCenter(page, center);
  for (const width of [320, 359, 360, 390, 640, 641, 650, 651, 760, 761, 1000, 1001, 1064, 1440, 1450, 1800]) {
    await page.setViewportSize({ width, height: 900 });
    const overflow = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth, nodes: [...document.querySelectorAll('body *')].map(node => ({ tag: node.tagName, id: node.id, class: node.className, right: node.getBoundingClientRect().right })).filter(node => node.right > innerWidth && typeof node.class === 'string').slice(0, 8) }));
    expect(overflow.width <= overflow.viewport, `Center overflow at ${width}: ${JSON.stringify(overflow.nodes)}`).toBe(true);
  }
  const evidence = testInfo.outputPath('fixtures');
  await mkdir(evidence, { recursive: true });
  await page.setViewportSize({ width: 1064, height: 750 });
  await page.screenshot({ path: `${evidence}/center-desktop-fixture.png` });
  await page.setViewportSize({ width: 320, height: 844 });
  await page.screenshot({ path: `${evidence}/center-320-fixture.png` });
  await page.locator('#newWorkButton').click();
  await expect(page.locator('#newWorkTitle')).toBeFocused();
  await expect.poll(() => page.locator('.ac-dialog[data-state="open"]').evaluate(node => getComputedStyle(node).opacity)).toBe('1');
  const form = page.locator('#newWorkForm');
  const modal = await page.locator('.ac-dialog[data-state="open"]').boundingBox();
  expect(modal.x).toBeGreaterThanOrEqual(0); expect(modal.y).toBeGreaterThanOrEqual(0);
  expect(modal.x + modal.width).toBeLessThanOrEqual(320); expect(modal.y + modal.height).toBeLessThanOrEqual(844);
  expect(await form.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `${evidence}/long-form-320-fixture.png` });
  await page.locator('#newWorkDialog .dialog-close').first().click();
  await page.setViewportSize({ width: 532, height: 844 });
  await page.addStyleTag({ content: 'html{font-size:32px!important}' });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator('#newWorkButton').click();
  expect(await form.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
  await expect.poll(() => page.locator('.ac-dialog[data-state="open"]').evaluate(node => getComputedStyle(node).opacity)).toBe('1');
  await page.locator('#newWorkForm [name="direction"]').scrollIntoViewIfNeeded();
  await expect(page.locator('#newWorkForm [name="direction"]')).toBeInViewport();
  await page.locator('#newWorkForm [type="submit"]').scrollIntoViewIfNeeded();
  await expect(page.locator('#newWorkForm [type="submit"]')).toBeInViewport();
  await page.screenshot({ path: `${evidence}/long-form-enlarged-text-fixture.png` });
  await page.locator('#newWorkDialog .dialog-close').first().click();
  // A 1064x750 desktop at 200% browser zoom has a 532x375 CSS viewport.
  await page.addStyleTag({ content: 'html{font-size:16px!important}' });
  await page.setViewportSize({ width: 532, height: 375 });
  await page.locator('#newWorkButton').click();
  await expect.poll(() => page.locator('.ac-dialog[data-state="open"]').evaluate(node => getComputedStyle(node).opacity)).toBe('1');
  expect(await page.locator('#newWorkForm .work-layout').evaluate(node => node.clientHeight)).toBeGreaterThanOrEqual(120);
  const assertReadableBelowHeader = async locator => {
    await expect(locator).toBeInViewport({ ratio: 1 });
    const box = await locator.boundingBox(), header = await page.locator('#newWorkForm .dialog-header').boundingBox();
    expect(box.y).toBeGreaterThanOrEqual(header.y + header.height);
    expect(box.y + box.height).toBeLessThanOrEqual(375);
  };
  await page.locator('#newWorkForm [name="count"]').scrollIntoViewIfNeeded();
  await assertReadableBelowHeader(page.locator('#newWorkForm [name="count"]'));
  await page.locator('#newWorkForm [name="direction"]').scrollIntoViewIfNeeded();
  await assertReadableBelowHeader(page.locator('#newWorkForm [name="direction"]'));
  await page.screenshot({ path: `${evidence}/long-form-200-percent-fields-fixture.png` });
  await page.locator('#newWorkForm [type="submit"]').scrollIntoViewIfNeeded();
  await assertReadableBelowHeader(page.locator('#newWorkForm [type="submit"]'));
  await expect(page.locator('#newWorkDialog .dialog-close').first()).toBeInViewport({ ratio: 1 });
  await page.screenshot({ path: `${evidence}/long-form-200-percent-fixture.png` });
  await page.locator('#newWorkDialog .dialog-close').first().click();
  const touch = await browser.newContext({ hasTouch: true, viewport: { width: 1000, height: 900 } });
  const touchPage = await touch.newPage();
  try {
    await openCenter(touchPage, center);
    const targets = await touchPage.locator('#newWorkButton, #importButton, #queueNavButton, #settingsButton, .row-actions button').evaluateAll(nodes => nodes.map(node => { const box = node.getBoundingClientRect(); return { width: box.width, height: box.height }; }));
    for (const target of targets) expect(target.height).toBeGreaterThanOrEqual(44);
    await touchPage.screenshot({ path: `${evidence}/center-coarse-1000-fixture.png` });
  } finally { await touch.close(); }
  await testInfo.attach('center-responsive-fixture', { path: `${evidence}/center-320-fixture.png`, contentType: 'image/png' });
});

test('center retains session search and filter on return and explains unavailable records', async ({ page, center }) => {
  await openCenter(page, center);
  const name = await page.locator('.product-link').first().textContent();
  await page.locator('#productSearch').fill(name);
  await expect(page.locator('#searchStatus')).toContainText('1 products found');
  await page.locator('[data-focus-key="column:primary:status"]').selectOption('filter:unknown');
  await expect(page.locator('.product-row')).toHaveCount(1);
  await expect(page.locator('.status-explanation')).toHaveCount(0);
  await page.locator('.product-link').click();
  await expect(page.locator('#journalBackLink')).toBeVisible();
  await page.locator('#journalBackLink').click();
  await expect(page.locator('#productSearch')).toHaveValue(name);
  await expect(page.locator('[data-focus-key="column:primary:status"]')).toHaveValue('filter:unknown');
  await page.locator('#productSearch').fill('unmatched-query');
  await expect(page.locator('#listState')).toContainText('unmatched-query');
  await expect(page.locator('#listState')).toContainText('Status unavailable');
  await page.locator('#listState button').click();
  await expect(page.locator('#productSearch')).toHaveValue('');
  await expect(page.locator('#productSearch')).toBeFocused();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.recent-work').first()).toHaveAttribute('data-label', 'Latest work');
});

test('center refresh failure preserves last successful data time and retries in place', async ({ page, center }) => {
  await openCenter(page, center);
  const observed = await page.locator('#observedAt').getAttribute('title');
  const count = await page.locator('.product-row').count();
  let fail = true;
  await page.route('**/api/center/v1/entries?*', async route => fail ? route.fulfill({ status: 503, json: { code: 'UNAVAILABLE' } }) : route.continue());
  await expect(page.locator('#connectionNotice')).toBeVisible({ timeout: 8000 });
  await expect(page.locator('.product-row')).toHaveCount(count);
  await expect(page.locator('#observedAt')).toHaveAttribute('title', observed);
  await expect(page.locator('#connectionNotice')).toContainText('last records');
  fail = false;
  await page.locator('#connectionNotice button').click();
  await expect(page.locator('#connectionNotice')).toBeHidden();
});

test('center validation links field errors and guards repeated batch submission', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  const input = page.locator('#newWorkForm [name="count"]');
  await input.fill('0');
  await page.locator('#newWorkForm [type="submit"]').click();
  await expect(input).toHaveAttribute('aria-invalid', 'true');
  const errorId = await input.getAttribute('aria-describedby');
  await expect(page.locator(`[id="${errorId}"]`)).toContainText('between 1 and 100');
  await input.fill('1');
  await expect(input).not.toHaveAttribute('aria-invalid', 'true');
  let writes = 0;
  await page.route('**/api/center/v1/explorations/batch', async route => {
    writes += 1;
    await new Promise(resolve => setTimeout(resolve, 800));
    await route.fulfill({ status: 503, json: { code: 'CONTEXT_UNAVAILABLE' } });
  });
  const idleWidth = (await page.locator('#newWorkForm [type="submit"]').boundingBox()).width;
  await page.locator('#newWorkForm [type="submit"]').click();
  await expect(page.locator('#newWorkForm')).toHaveAttribute('aria-busy', 'true');
  expect((await page.locator('#newWorkForm [type="submit"]').boundingBox()).width).toBe(idleWidth);
  await page.locator('#newWorkForm').evaluate(form => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
  await expect(page.locator('#newWorkForm .form-status')).toContainText('Action did not complete', { timeout: 15000 });
  expect(writes).toBe(1);
  await expect(input).toHaveValue('1');
});

test('center automatic reading can be paused and manually resumed without losing records', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#settingsButton').click();
  await page.locator('#centerAutoRefresh-control').uncheck();
  await page.locator('#settingsDialog .dialog-close').first().click();
  let reads = 0;
  page.on('request', request => { if (request.url().endsWith('/api/center/v1/summary')) reads += 1; });
  await page.waitForTimeout(5400);
  expect(reads).toBe(0);
  await page.reload();
  await expect(page.locator('#observedAt')).not.toBeEmpty();
  await page.locator('#settingsButton').click();
  await expect(page.locator('#centerAutoRefresh-control')).not.toBeChecked();
  const before = reads;
  await page.locator('#centerRefreshButton').click();
  await expect.poll(() => reads).toBeGreaterThan(before);
  await expect(page.locator('#observedAt')).toContainText('Read at');
});

test('center restores reading position and moves focus when a refreshed product disappears', async ({ page, center }) => {
  let removeFirst = false;
  await page.route('**/api/center/v1/entries?*', async route => {
    const response = await route.fetch(), payload = await response.json(), original = payload.data.items[0];
    payload.data.items = Array.from({ length: 24 }, (_, index) => ({ ...original, entryId: index ? `${original.entryId}-${index}` : original.entryId, displayName: `Product ${index + 1}` }));
    if (removeFirst) payload.data.items.shift();
    payload.data.total = payload.data.items.length; payload.data.nextCursor = null;
    await route.fulfill({ json: payload });
  });
  await openCenter(page, center);
  await page.getByRole('button', { name: /Show all/ }).click();
  await expect.poll(() => page.locator('.other-products-disclosure').evaluate(node => node.getAnimations({ subtree: true }).length)).toBe(0);
  await page.evaluate(() => window.scrollTo(0, 500));
  await page.locator('.product-link').first().evaluate(link => link.click());
  await expect(page.locator('#journalBackLink')).toBeVisible();
  await page.locator('#journalBackLink').click();
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(400);
  await page.locator('.product-link').first().focus();
  removeFirst = true;
  await expect(page.locator('.product-link').first()).toHaveText('Product 2', { timeout: 8000 });
  await expect(page.locator('.product-link').first()).toBeFocused();
  await expect(page.locator('#searchStatus')).toContainText('Focus moved');
});

test('D catalog separates runtime from latest round, keeps title navigation and fits mobile', async ({ page, center }) => {
  await openCenter(page, center);
  const row = page.locator('.product-row').first();
  await expect(page.locator('.center-header #queueNavButton')).toHaveCount(0);
  await expect(row.locator('.row-actions a')).toHaveCount(0);
  await expect(row.locator('.latest-round')).toContainText('#06');
  await expect(row.locator('.latest-round')).toContainText('Completed');
  await expect(row.locator('.status-cell')).not.toContainText('Completed');
  await page.locator('#productSearch').fill('no-such-product');
  await expect(page.locator('.product-row')).toHaveCount(0);
  await page.locator('#productSearch').fill('');
  await expect(row).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#capacityForm')).toBeVisible();
  await page.locator('#closeQueueButton').click();
  await row.locator('.product-link').click();
  await expect(page.locator('#cycleNumber')).toHaveText('06');
  await expect(page.locator('#runHeading')).toHaveCount(0);
  await expect(page.locator('#historyList .history-row .progress-completed')).toHaveCount(5);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('D reference keeps recent products independent of running state and uses compact geometry', async ({ page, center }) => {
  await page.route('**/api/center/v1/entries?*', async route => {
    const response = await route.fetch();
    const payload = await response.json();
    const entry = payload.data.items[0];
    payload.data.items = Array.from({ length: 6 }, (_, index) => ({ ...entry,
      entryId: index ? `${entry.entryId}-${index}` : entry.entryId,
      displayName: `Product ${index + 1}`, executionSummary: { state: 'unknown' },
      latestCycleStatus: ['completed', 'pending', 'interrupted', 'completed_with_timeout', 'failed', 'unknown'][index],
      lastActivityAt: `2026-09-${String(26 - index).padStart(2, '0')}T01:00:00Z`,
    }));
    payload.data.total = 6; payload.data.nextCursor = null;
    await route.fulfill({ json: payload });
  });
  await page.setViewportSize({ width: 1064, height: 750 });
  await openCenter(page, center);
  const groups = page.locator('.product-group');
  await expect(groups).toHaveCount(2);
  await expect(groups.nth(0).locator('h2')).toHaveText('Recent products4');
  await expect(groups.nth(1).locator('h2')).toHaveText('Other products2');
  await expect(groups.nth(0).locator('.product-row')).toHaveCount(4);
  await expect(groups.nth(1).locator('.product-row')).toHaveCount(2);
  await expect(groups.nth(0).locator('.latest-round .status-symbol')).toHaveClass([
    'status-symbol completed', 'status-symbol queued', 'status-symbol paused', 'status-symbol paused',
  ]);
  expect((await page.locator('.header-inner').boundingBox()).height).toBe(56);
  // Unknown-state reasons must remain readable; 66px is a minimum, not a cap.
  expect((await groups.nth(0).locator('.product-row').first().boundingBox()).height).toBeGreaterThanOrEqual(66);
  await expect(page.locator('.status-explanation')).toHaveCount(0);
  const fonts = await page.locator('.product-name').first().evaluate(node => ({ family: getComputedStyle(node).fontFamily, size: getComputedStyle(node).fontSize }));
  expect(fonts.family).toContain('Arial'); expect(fonts.size).toBe('18px');
  await page.locator('#productSearch').fill('Product 6');
  await expect(page.locator('.product-row')).toHaveCount(1);
  await expect(page.locator('.product-link')).toHaveText('Product 6');
  await page.locator('#productSearch').fill('');
  await page.locator('#profileButton').click();
  await expect(page.getByRole('menuitem', { name: 'Settings', exact: true })).toHaveCount(0);
  await page.keyboard.press('Escape');
  await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsDialog')).toBeVisible();
});

test('expired active evidence is unconfirmed rather than zero running', async ({ page, center }) => {
  await page.route('**/api/center/v1/summary', async route => {
    const payload = await (await route.fetch()).json();
    payload.data.currentRequests = [{ requestId: 'expired-request', entryId: center.entryId,
      state: 'running', liveConfirmedAt: '2000-01-01T00:00:00Z' }];
    payload.data.occupiedCount = 1;
    await route.fulfill({ json: payload });
  });
  await openCenter(page, center);
  await expect(page.locator('#capacitySummary')).toHaveText('Runtime status unconfirmed');
});

test('configuration templates persist, mixed groups freeze settings, and clearing default uses last submission', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  const first = page.locator('.work-group').first();
  await first.locator('[name="engine"]').selectOption('codex');
  await first.locator('[name="model"]').fill('gpt-6.1-sol');
  await first.locator('[name="effort"]').selectOption('high');
  await first.locator('.template-manage-toggle').click();
  await first.locator('.template-name').fill('My high configuration');
  await first.getByRole('button', { name: 'Save template', exact: true }).click();
  await expect(first.locator('.template-status')).toHaveText('Template settings saved.');
  await first.getByRole('button', { name: 'Set as default', exact: true }).click();
  await expect(first.locator('.template-select option:checked')).toContainText('Default');
  await first.locator('[name="count"]').fill('2');
  await page.locator('#addWorkGroup').click();
  const second = page.locator('.work-group').nth(1);
  await expect(second.locator('[name="model"]')).toHaveValue('gpt-6.1-sol');
  await second.locator('[name="effort"]').selectOption('xhigh');
  await second.locator('[name="count"]').fill('2');
  const sent = page.waitForRequest(request => request.url().endsWith('/explorations/batch') && request.method() === 'POST');
  await page.locator('#newWorkForm > .dialog-actions [type="submit"]').click();
  const batch = (await sent).postDataJSON();
  expect(batch.groups.map(group => [group.count, group.config.effort, group.direction])).toEqual([[2, 'high', ''], [2, 'xhigh', '']]);
  await expect(page.locator('#newWorkDialog')).not.toBeVisible();
  await page.reload();
  await expect(page.locator('#observedAt')).not.toBeEmpty();
  await page.locator('#newWorkButton').click();
  await expect(page.locator('.work-group').first().locator('[name="effort"]')).toHaveValue('high');
  await page.locator('#newWorkDialog .dialog-close').first().click();
  await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsForm .template-select')).toBeVisible();
  await page.locator('#settingsForm .template-editor .disclosure-trigger').click();
  await page.getByRole('button', { name: 'Clear default template', exact: true }).click();
  await expect(page.locator('#settingsForm .template-status')).toHaveText('Template settings saved.');
  await page.locator('#settingsDialog .dialog-close').first().click();
  await page.locator('#newWorkButton').click();
  await expect(page.locator('.work-group').first().locator('[name="effort"]')).toHaveValue('xhigh');
  const prefs = (await (await page.request.get(`${center.url}/api/center/v1/preferences`)).json()).data;
  expect(prefs.templates[0].config.effort).toBe('high');
  expect(prefs.templates[0].config).not.toHaveProperty('direction');
});

test('concurrency is editable in the existing queue and unlimited persists across reload', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#capacityForm [name="capacity"]')).toHaveValue('4');
  await page.locator('#capacityForm [name="capacity"]').fill('2');
  await page.locator('#capacityForm [type="submit"]').click();
  await expect(page.locator('#capacityForm .form-status')).toHaveText('Concurrency updated.');
  await page.locator('#capacityForm [role="checkbox"]').check();
  await page.locator('#capacityForm [type="submit"]').click();
  await expect.poll(async () => (await (await page.request.get(`${center.url}/api/center/v1/summary`)).json()).data.maxConcurrentProjects).toBeNull();
  await page.reload();
  await expect(page.locator('#observedAt')).not.toBeEmpty();
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#capacityForm [role="checkbox"]')).toBeChecked();
  await expect(page.locator('#capacityForm [name="capacity"]')).toBeDisabled();
});

test('group editor preserves drafts, supports keyboard switching, and reveals invalid hidden fields', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  const first = page.locator('.work-group').first();
  await first.locator('[name="count"]').fill('2');
  await first.locator('[name="direction"]').fill('First direction');
  await first.locator('[name="model"]').fill('gpt-6.1-sol');
  await page.locator('#addWorkGroup').click();
  let second = page.locator('.work-group').nth(1);
  await second.locator('[name="effort"]').selectOption('xhigh');
  await second.locator('[name="direction"]').fill('Second direction');
  await second.locator('[data-count-step="1"]').click();
  await expect(page.locator('#workBatchSummary')).toHaveText('4 projects · 2 groups');
  await page.locator('#workGroupTabs [role="tab"]').first().click();
  await expect(first).toBeVisible();
  await expect(second).not.toBeVisible();
  await expect(first.locator('[name="direction"]')).toHaveValue('First direction');
  await expect(first.locator('[name="model"]')).toHaveValue('gpt-6.1-sol');
  await page.locator('#workGroupTabs [role="tab"]').first().press('ArrowDown');
  await expect(second.locator('[name="direction"]')).toHaveValue('Second direction');
  await expect(second.locator('[name="effort"]')).toHaveValue('xhigh');
  await second.locator('.remove-group').click();
  await expect(first).toBeVisible();
  await expect(first.locator('.remove-group')).not.toBeVisible();
  await page.locator('#addWorkGroup').click();
  second = page.locator('.work-group').nth(1);
  await expect(second.locator('[name="direction"]')).toHaveValue('');
  await expect(second.locator('[name="effort"]')).toHaveValue('high');
  await second.locator('[name="count"]').fill('2');
  await page.locator('#workGroupTabs [role="tab"]').first().click();
  await first.locator('[name="count"]').fill('99');
  const submit = page.locator('#newWorkForm [type="submit"]');
  await expect(submit).toBeDisabled();
  await first.locator('[name="count"]').fill('0');
  await page.locator('#workGroupTabs [role="tab"]').nth(1).click();
  await submit.click();
  await expect(first).toBeVisible();
  await expect(first.locator('[name="count"]')).toBeFocused();
  await first.locator('[name="count"]').fill('2');
  const sent = page.waitForRequest(request => request.url().endsWith('/explorations/batch') && request.method() === 'POST');
  await submit.click();
  expect((await sent).postDataJSON().groups.map(group => [group.count, group.direction])).toEqual([[2, 'First direction'], [2, '']]);
});

test('Chinese batch and queue controls fit desktop and narrow screens', async ({ page, center }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await openCenter(page, center);
  await page.locator('#settingsButton').click();
  await page.locator('#settingsForm [name="language"]').selectOption('zh-CN');
  await page.locator('#settingsForm [type="submit"]').click();
  await expect(page.locator('#settingsDialog')).not.toBeVisible();
  await page.locator('#newWorkButton').click();
  await expect(page.locator('.work-group [name="effort"]')).toHaveValue('high');
  await expect(page.locator('#newWorkForm [type="submit"]')).toBeInViewport();
  const editor = page.locator('.work-group');
  expect((await editor.locator('[name="engine"]').boundingBox()).y).toBeLessThan((await editor.locator('[name="model"]').boundingBox()).y);
  expect((await editor.locator('[name="productLanguage"]').boundingBox()).y).toBeLessThan((await editor.locator('[name="effort"]').boundingBox()).y);
  await page.screenshot({ path: testInfo.outputPath('dialog-b-desktop-zh.png') });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator('#addWorkGroup').click();
  await expect(page.locator('.work-group')).toHaveCount(2);
  expect(await page.locator('#newWorkDialog').evaluate(node => node.scrollWidth <= node.clientWidth)).toBeTruthy();
  await expect(page.locator('#newWorkForm [type="submit"]')).toBeInViewport();
  await page.screenshot({ path: testInfo.outputPath('dialog-b-narrow-zh.png') });
  await page.locator('#newWorkDialog .dialog-close').first().click();
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#capacityForm [type="submit"]')).toBeVisible();
  await expect.poll(() => page.locator('[data-slot=sheet-content]').evaluate(node => Math.round(node.getBoundingClientRect().left))).toBe(0);
  expect(await page.locator('#capacityForm').evaluate(node => node.scrollWidth <= node.clientWidth)).toBeTruthy();
  await page.screenshot({ path: testInfo.outputPath('queue-narrow-zh.png') });
});

test('default autonomous creation uses empty text and preserves preparation failures after reload', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  const created = page.waitForRequest(request => request.url().endsWith('/api/center/v1/explorations/batch') && request.method() === 'POST');
  await page.locator('#newWorkForm [type="submit"]').click();
  expect((await created).postDataJSON().groups[0].direction).toBe('');
  await expect(page.locator('#newWorkDialog')).not.toBeVisible();
  await expect(page.locator('#queueContent')).toContainText(/framework|框架/i);
  const response = await page.request.get(`${center.url}/api/center/v1/operations`);
  const operations = (await response.json()).data.items;
  expect(operations).toHaveLength(1);
  expect(operations[0].state).toBe('failed');
  expect(operations[0].reason).toBe('FRAMEWORK_UNVERIFIED');
  expect(operations[0]).not.toHaveProperty('input');
  await page.reload();
  await expect(page.locator('#observedAt')).not.toBeEmpty();
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#queueContent')).toContainText(/framework|框架/i);
  expect((await (await page.request.get(`${center.url}/api/center/v1/requests`)).json()).data.items).toHaveLength(0);
});

test('six product rounds retain earliest history and complete usage independently of visible rows', async ({ page, center }) => {
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#historyList [data-disclosure]')).toHaveCount(5);
  await page.locator('#tab-usage').click();
  await page.locator('#usagePeriod').selectOption('all');
  await expect(page.locator('#usageSummary .usage-group')).toHaveCount(6);
  await expect(page.locator('#usageSummary')).toContainText('1 of 1');
  await expect(page.locator('#usageRows tr')).toHaveCount(6);
  expect(await page.locator('#usageRows tr').evaluateAll(rows => rows.reduce((sum, row) => sum + Number(row.cells[5].textContent.replace(/,/g, '')), 0))).toBe(60);
  const raw = await page.request.get(`${center.url}/api/center/v1/entries/${center.entryId}/resources/log-${center.firstCycleId}?sourceId=${center.sourceId}`);
  expect(raw.ok()).toBeTruthy();
  expect(await raw.text()).toContain('projects/one private log');
});

test('healthy product preview is a separate loopback link, never an artifact document URL', async ({ page, center }) => {
  await page.goto(`${center.url}/products/${center.entryId}`);
  const preview = page.locator(`a[href="${center.previewUrl}"]`);
  await expect(preview).toBeVisible();
  await expect(preview).toHaveAttribute('rel', /noopener/);
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

test('an owned attention dispatch retains stop controls', async ({ page, center }) => {
  await queueFixture(page, center, true);
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#stopAllButton')).toBeEnabled();
  await expect(page.locator('#queueContent button').filter({ hasText: /^Stop/ })).toBeVisible();
});

test('automatic refresh preserves focused product-menu and queue actions', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const view = page.locator('.product-link').first();
  await view.focus();
  await page.waitForTimeout(5500);
  await expect(view).toBeFocused();
  const queuedProduct = page.locator('.queue-preview-name').first();
  await queuedProduct.focus();
  await page.waitForTimeout(5500);
  await expect(queuedProduct).toBeFocused();
  await page.locator('.product-row .more-button').first().click();
  const action = page.locator('[role=menuitem]:not([data-disabled])').first();
  await action.focus();
  const label = await action.textContent();
  await page.waitForTimeout(5500);
  expect(await page.evaluate(() => document.activeElement?.textContent)).toBe(label);
  await action.press('Escape');
  await page.locator('#queueNavButton').click();
  const cancel = page.locator('#queueContent button').filter({ hasText: /^Cancel$/ });
  await cancel.focus();
  await page.waitForTimeout(5500);
  await expect(cancel).toBeFocused();
});

test('preparing start-now work can be stopped before a request exists', async ({ page, center }) => {
  const send = (route, data) => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ schemaVersion: 1,
    centerId: 'fixture', revision: 1, observedAt: new Date().toISOString(), data }) });
  await page.route('**/api/center/v1/operations', route => send(route, { items: [{ operationId: 'preparing-fixture',
    kind: 'exploration', state: 'preparing', createdAt: new Date().toISOString(), revision: 1 }] }));
  await page.route('**/api/center/v1/summary', route => send(route, { language: 'en', dispatchEnabled: false,
    queueRevision: 1, executionAvailable: true, currentRequest: null, queuedCount: 0, attentionCount: 0, preparationCount: 1 }));
  await openCenter(page, center);
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#stopAllButton')).toBeEnabled();
  await expect(page.locator('#queueNavCount')).toHaveText('1');
});

test.describe('long product history', () => {
  test.use({ centerCycles: 36 });
  test('limited older rows load their recorded detail and keep scoped logs', async ({ page, center }) => {
    await page.goto(`${center.url}/products/${center.entryId}`);
    await expect(page.locator('#historyList [data-disclosure]')).toHaveCount(35);
    const oldest = page.locator('#historyList [data-disclosure]').last();
    await oldest.locator('.disclosure-trigger').click();
    await expect(oldest).toContainText('Recorded fixture detail 1');
    await page.locator('#tab-usage').click();
    await page.locator('#usagePeriod').selectOption('all');
    await expect(page.locator('#usageSummary .usage-group')).toHaveCount(36);
    await expect(page.locator('#usageSummary')).toContainText('1 of 1');
    await expect(page.locator('#usageRows tr')).toHaveCount(36);
    expect(await page.locator('#usageRows tr').evaluateAll(rows => rows.reduce((sum, row) => sum + Number(row.cells[5].textContent.replace(/,/g, '')), 0))).toBe(360);
  });
});

test.describe('continuous linked exploration history', () => {
  test.use({ centerExplorationCycles: 3 });
  test('default product page includes exploration and retains its original scoped log', async ({ page, center }) => {
    await page.goto(`${center.url}/products/${center.entryId}`);
    await expect(page.locator('#historyList [data-disclosure]')).toHaveCount(8);
    await expect(page.locator('#cycleNumber')).toHaveText('09');
    await expect(page.locator('#historyList .history-number-value')).toHaveText(['08', '07', '06', '05', '04', '03', '02', '01']);
    const earliest = page.locator('#historyList [data-disclosure]').last();
    await earliest.locator('.disclosure-trigger').click();
    await expect(earliest).toContainText('Recorded exploration detail 1');
    const endpoint = `${center.url}/api/center/v1/entries/${center.entryId}`;
    const journal = (await (await page.request.get(`${endpoint}/journal?limit=100`)).json()).data;
    expect(journal.cycles).toHaveLength(9);
    expect(journal.cycles.slice(-3).map(row => row.id)).toEqual([...center.explorationCycleIds].reverse());
    expect(journal.cycles[0].number).toBe(6);
    expect(journal.cycles[0].sequenceNumber).toBe(9);
    const selected = (await (await page.request.get(`${endpoint}/journal?section=exploration&limit=100&sourceId=${center.sourceId}`)).json()).data;
    expect(selected.cycles.map(row => row.id)).toEqual([...center.explorationCycleIds].reverse());
    const log = await page.request.get(new URL(journal.cycles.at(-1).logUrl, center.url).href);
    expect(log.ok()).toBeTruthy();
    expect(await log.text()).toBe('exploration private log');
  });
});


test('shared shadcn menus and dialogs preserve focus, form nodes and keyboard boundaries', async ({ page, center }) => {
  await openCenter(page, center);
  await expect(page.locator('html')).toHaveAttribute('data-ui', 'shadcn');
  const trigger = page.locator('.product-row .more-button').first();
  await trigger.click();
  await page.getByRole('menuitem', { name: 'Manage sources', exact: true }).click();
  await expect(page.locator('[data-slot=dialog-content]')).toBeVisible();
  await page.locator('#sourceDialog button').first().press('Escape');
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page.getByRole('menuitem', { name: 'Archive', exact: true }).click();
  await expect(page.getByRole('alertdialog')).toBeVisible();
  await page.locator('#confirmDialog .dialog-close').first().press('Escape');
  await expect(trigger).toBeFocused();
  await page.locator('#importButton').click();
  await page.locator('#importForm [name=root]').fill('draft-path');
  await page.locator('#importForm [name=root]').press('Tab');
  expect(await page.evaluate(() => Boolean(document.activeElement?.closest('[data-slot=dialog-content]')))).toBeTruthy();
  await page.locator('#importDialog .dialog-close').first().click();
  await expect(page.locator('#importButton')).toBeFocused();
  await expect(page.locator('#importForm [name=root]')).toHaveValue('draft-path');
  await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
  await page.locator('#importButton').click();
  await expect(page.locator('#importForm [name=root]')).toHaveValue('');
  await page.locator('#importForm [name=root]').press('Escape');
  await expect(page.locator('#importButton')).toBeFocused();
});

test('standard controls own selection, reset, notifications and product search', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('#newWorkButton').click();
  const form = page.locator('#newWorkForm');
  await expect(form.locator('[data-slot=native-select-wrapper] select').first()).toBeVisible();
  const choices = form.getByRole('radio');
  await expect(choices).toHaveCount(2);
  await expect(choices.last()).toBeChecked();
  await choices.last().focus(); await page.keyboard.press('ArrowLeft', { delay: 80 });
  await expect(choices.first()).toBeChecked();
  expect(await form.evaluate(node => new FormData(node).get('executionMode'))).toBe('start_now');
  await page.keyboard.press('Escape');
  await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
  await page.locator('#newWorkButton').click();
  await expect(choices.last()).toBeChecked();
  await page.locator('#addWorkGroup').click();
  await expect(form.locator('.work-group:not([hidden]) [data-slot=native-select-wrapper] select').first()).toBeVisible();
  await expect(form.getByRole('radio')).toHaveCount(2);
  await page.keyboard.press('Escape');
  await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsForm').getByRole('switch')).toHaveCount(1);
  await page.locator('#settingsForm [type=submit]').click();
  await expect(page.locator('[data-sonner-toast]')).toContainText('saved');
  await page.goto(`${center.url}/products/${center.entryId}`);
  await page.locator('#productSwitcherButton').click();
  await expect(page.locator('#productSwitcherControls [cmdk-list]').getByRole('option').first()).toBeVisible();
  const search = page.locator('#productSwitcherControls [cmdk-input]');
  await search.fill('unmatched-product-123');
  await expect(page.locator('[cmdk-empty]')).toBeVisible();
  await search.fill('');
  await expect(page.locator('#productSwitcherControls [cmdk-item]').first()).toBeVisible();
  await search.press('ArrowDown', { delay: 80 });
  await expect(page.locator('#productSwitcherControls [cmdk-item][aria-selected=true]')).toHaveCount(1);
  await search.press('Enter');
  await expect(page.locator('#cycleTitle')).toBeVisible();
  await page.locator('#productSwitcherButton').click();
  await expect(page.locator('#productSwitcherControls [cmdk-item]').first()).toBeVisible();
  await search.press('Escape'); await expect(page.locator('#productSwitcherButton')).toBeFocused();
});

test('catalog controls preserve search, preview choice and whole-row navigation', async ({ page, center }) => {
  await openCenter(page, center);
  const search = page.locator('#productSearch');
  await page.mouse.move(0, 0);
  await expect.poll(async () => (await search.boundingBox()).width).toBeLessThan(50);
  await search.hover();
  await expect.poll(async () => (await search.boundingBox()).width).toBeGreaterThan(180);
  await search.fill('fixture');
  await page.locator('.brand').focus(); await page.mouse.move(0, 0);
  await expect.poll(async () => (await search.boundingBox()).width).toBeGreaterThan(180);
  await search.fill(''); await page.locator('.brand').focus(); await page.mouse.move(0, 0);
  await expect.poll(async () => (await search.boundingBox()).width).toBeLessThan(50);
  const filters = page.locator('#filters');
  await filters.locator('[data-filter=running]').click();
  await expect(filters.locator('[data-state=on]')).toHaveCount(1);
  await filters.locator('[data-filter=all]').click();
  await filters.locator('[data-filter=all]').click();
  await expect(filters.locator('[data-state=on]')).toHaveCount(1);
  await filters.locator('[data-filter=all]').focus(); await page.keyboard.press('ArrowRight'); await expect(filters.locator('[data-filter=running]')).toBeFocused(); await page.keyboard.press('Space');
  await expect(filters.locator('[data-filter=running]')).toHaveAttribute('data-state', 'on');
  await filters.locator('[data-filter=all]').click();
  const preview = page.locator('.preview-select').first();
  await preview.selectOption('none');
  await expect(page.locator('.product-example > *')).toHaveCount(0);
  await preview.selectOption('logo');
  await expect(page.locator('.product-example .product-icon').first()).toBeVisible();
  await preview.selectOption('screenshot');
  const row = page.locator(`.product-row[data-entry-id="${center.entryId}"]`);
  await row.locator('.recent-work').click();
  await expect(page).toHaveURL(`${center.url}/products/${center.entryId}`);
  await expect.poll(() => page.evaluate(() => window.DashboardNavigation.inspect().active)).toBe('journal');
  await expect.poll(() => page.evaluate(() => window.DashboardNavigation.inspect().transitioning)).toBe(false);
  await expect(page.locator('#projectName')).toBeVisible();
  expect(await page.locator('#journalBackLink').evaluate(node => !!node.closest('.topbar'))).toBeTruthy();
  const history = page.locator('#historyList .history-row').first();
  await history.locator('.disclosure-trigger').click();
  await expect(history.locator('.cycle-report-surface')).toBeVisible();
  await expect(history.locator('.cycle-report-footer .cycle-log-link')).toBeVisible();
  const surfaces = await page.locator('.cycle-report-surface').evaluateAll(nodes => nodes.filter(n => n.offsetParent).map(n => getComputedStyle(n).backgroundColor));
  expect(new Set(surfaces).size).toBe(1);
  await page.locator('#journalBackLink').click();
  await expect(page.locator('.preview-select').first()).toHaveValue('screenshot');
  await expect(page.locator('#queueSidebarContent .queue-empty')).toHaveCount(0);
  for (const width of [390, 1359]) {
    await page.setViewportSize({ width, height: 919 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
});

test('reviewed layouts use white fields, compact settings and continuous product history', async ({ page, center }) => {
  await page.emulateMedia({ colorScheme: 'dark' });
  await openCenter(page, center);
  await expect(page.locator('.product-group-title').first()).toContainText('Recent products');
  const headings = await page.locator('.product-head').first().locator('th').allTextContents();
  expect(headings.map(text => text.trim().split('\n')[0])).toEqual(expect.arrayContaining(['Name', 'Latest work', 'Updated']));
  expect(headings[2]).toMatch(/^Runtime/);
  expect(headings[3]).toMatch(/Latest round/);
  await expect(page.locator('#capacitySummary')).toBeAttached();
  expect(await page.locator('#capacitySummary').evaluate(node => !!node.closest('.queue-sidebar'))).toBeTruthy();
  await expect(page.locator('.catalog-footer')).toHaveCount(0);
  expect(await page.locator('#productSearch').evaluate(node => getComputedStyle(node).backgroundColor)).toBe('rgba(0, 0, 0, 0)');
  await page.locator('#settingsButton').click();
  await expect(page.locator('#settingsForm').getByRole('switch')).toBeVisible();
  for (const width of [1359, 390]) {
    await page.setViewportSize({ width, height: 919 });
    await expect.poll(async () => {
      const rect = await page.locator('#settingsForm').boundingBox();
      return rect.x >= 0 && rect.x + rect.width <= width;
    }).toBeTruthy();
    await expect(page.locator('#settingsForm [type=submit]')).toBeInViewport();
  }
  await page.keyboard.press('Escape');
  await expect(page.locator('#settingsButton')).toBeFocused();
  await page.setViewportSize({ width: 1359, height: 919 });
  await page.goto(`${center.url}/products/${center.entryId}`);
  await expect(page.locator('#projectName')).toBeVisible();
  await expect(page.locator('#runtimeNotice')).toBeHidden();
  await expect(page.locator('.history-number .cycle-date')).toHaveCount(0);
  await expect(page.locator('.cycle-records h3')).toHaveCount(0);
  const layout = await page.evaluate(() => {
    const tabs = document.querySelector('[data-slot=tabs-list]');
    const node = document.querySelector('.history-row .progress-node');
    return { tabsScroll: ['auto', 'scroll'].includes(getComputedStyle(tabs).overflowY) && tabs.scrollHeight > tabs.clientHeight, icon: node.querySelector('svg').getBoundingClientRect().height, node: node.getBoundingClientRect().height,
      statusInName: !!document.querySelector('#projectRuntimeStatus').closest('.project-identity'), overflow: document.documentElement.scrollWidth > innerWidth };
  });
  expect(layout.tabsScroll).toBeFalsy();
  expect(layout.icon).toBe(layout.node);
  expect(layout.statusInName).toBeTruthy();
  expect(layout.overflow).toBeFalsy();
});

test('catalog selection slides to the active filter and stays aligned after resizing', async ({ page, center }) => {
  await openCenter(page, center);
  const search = await page.locator('.search-field').boundingBox();
  const icon = await page.locator('.search-field svg').boundingBox();
  expect(icon.x + icon.width / 2).toBeCloseTo(search.x + search.width / 2, 0);
  await expect(page.locator('.example-heading')).toHaveCount(0);
  for (const filter of ['running', 'all']) {
    await page.locator(`.filter-button[data-filter="${filter}"]`).click();
    await expect.poll(async () => {
      const active = await page.locator('.filter-button[data-state=on]').boundingBox();
      const selection = await page.locator('.filter-selection').boundingBox();
      return Math.abs(active.x - selection.x) + Math.abs(active.y - selection.y) + Math.abs(active.width - selection.width);
    }).toBeLessThan(2);
  }
  await page.setViewportSize({ width: 390, height: 919 });
  await expect.poll(async () => {
    const active = await page.locator('.filter-button[data-state=on]').boundingBox();
    const selection = await page.locator('.filter-selection').boundingBox();
    return Math.abs(active.x - selection.x) + Math.abs(active.y - selection.y);
  }).toBeLessThan(2);
});

test('rapid targets, resize and reduced motion keep navigation and tab state coherent', async ({ page, center }) => {
  await openCenter(page, center);
  await page.evaluate(() => {
    for (const filter of ['running', 'queued', 'all']) document.querySelector(`.filter-button[data-filter="${filter}"]`).click();
  });
  await expect(page.locator('.filter-button[data-state=on]')).toHaveAttribute('data-filter', 'all');
  await expect(page.locator('.product-link')).toHaveCount(1);
  await page.locator('.product-link').click();
  await expect(page.locator('#journalBackLink')).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await expect(page.locator('#cycleTitle')).toBeVisible();
  await page.evaluate(() => { for (const name of ['usage', 'logs', 'work']) document.querySelector(`#tab-${name}`).click(); });
  await expect(page.locator('#tab-work')).toHaveAttribute('aria-selected', 'true');
  await expect(page.locator('#cycleTitle')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.locator('#journalBackLink').click();
  await page.locator('.product-link').click();
  await expect(page.locator('#cycleTitle')).toBeVisible();
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await page.locator('#settingsButton').click();
  await page.keyboard.press('Escape');
  await expect(page.locator('#settingsButton')).toBeFocused();
  await expect(page.locator('[data-motion-exit]')).toHaveCount(0);
});

test('backgrounding settles motion and missing animation APIs retain working links', async ({ page, center }) => {
  await openCenter(page, center);
  await page.locator('.product-link').click();
  await expect(page.locator('#journalBackLink')).toBeVisible();
  await page.evaluate(() => {
    Object.defineProperty(document, 'hidden', { configurable: true, value: true });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await expect(page.locator('html')).toHaveAttribute('data-motion-hidden', '');
  await page.evaluate(() => {
    delete document.hidden; document.dispatchEvent(new Event('visibilitychange'));
    document.querySelectorAll('.workspace-view[data-view=center] .product-row').forEach(row => row.remove());
  });
  await page.locator('#journalBackLink').click();
  await expect(page.locator('#productSearch')).toBeEnabled();
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await page.evaluate(() => { Element.prototype.animate = undefined; });
  await page.evaluate(url => DashboardNavigation.navigate(url), `${center.url}/products/${center.entryId}`);
  await expect(page.locator('#cycleTitle')).toBeVisible();
  await expect(page.locator('.workspace-motion-surface')).toHaveCount(0);
  await page.locator('#journalBackLink').click();
  await expect(page).toHaveURL(`${center.url}/center`);
});

for (const count of [100, 1000]) test(`synthetic ${count} products use bounded list motion and preserve the search field`, async ({ page, center }, testInfo) => {
  test.setTimeout(60000);
  await page.route('**/api/center/v1/entries?*', async route => {
    const payload = await (await route.fetch()).json(), original = payload.data.items[0];
    payload.data.items = Array.from({ length: count }, (_, index) => ({ ...original, entryId: `synthetic-${index}`, displayName: `Synthetic product ${index}` }));
    payload.data.total = count; payload.data.nextCursor = null;
    await route.fulfill({ json: payload });
  });
  await openCenter(page, center);
  await expect(page.locator('.product-row')).toHaveCount(count);
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  const measurement = await page.evaluate(async () => {
    const field = document.querySelector('#productSearch'), started = performance.now();
    document.querySelector('.other-products-disclosure .disclosure-trigger').click();
    const panel = document.querySelector('.other-products-disclosure [data-slot=collapsible-content]');
    const keyframes = panel.getAnimations().flatMap(animation => animation.effect.getKeyframes());
    await Promise.all(panel.getAnimations().map(animation => animation.finished.catch(() => {})));
    return { elapsed: performance.now() - started, keyframes, fieldSame: field === document.querySelector('#productSearch') };
  });
  expect(measurement.fieldSame).toBe(true);
  expect(measurement.keyframes.every(frame => !Object.hasOwn(frame, 'height'))).toBe(true);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
  await page.locator('#productSearch').fill(`Synthetic product ${count - 1}`);
  await expect(page.locator('.product-row')).toHaveCount(1);
  await expect(page.locator('#productSearch')).toBeFocused();
  await testInfo.attach('synthetic-list-motion.json', { body: JSON.stringify({ count, cpuRate: 4, ...measurement }, null, 2), contentType: 'application/json' });
});

for (const emptyCase of ['search', 'filter']) {
  test(`empty catalog ${emptyCase} action resets the view through real event wiring`, async ({ page, center }) => {
    const entry = { entryId: 'empty-action-fixture', kind: emptyCase === 'explorations' ? 'exploration' : 'product',
      displayName: 'Visible fixture', availability: 'available', executionSummary: { state: 'ended' } };
    await page.route('**/api/center/v1/entries?*', route => route.fulfill({ json: { schemaVersion: 1,
      data: { items: [entry], total: 1, nextCursor: null } } }));
    await openCenter(page, center);
    if (emptyCase === 'search') await page.locator('#productSearch').fill('no matching product');
    if (emptyCase === 'filter') await page.locator('[data-filter="archived"]').click();
    const action = page.locator('#listState button').first();
    await expect(action).toBeVisible();
    await action.click();
    await expect(page.locator('#productRows')).toContainText('Visible fixture');
    await expect(page.locator('#productSearch')).toHaveValue('');
    await expect(action).toHaveCount(0);
    if (emptyCase !== 'explorations') await expect(page.locator('[data-filter="all"]')).toHaveAttribute('data-state', 'on');
  });
}

for (const change of ['path', 'mode', 'close', 'escape']) {
  for (const outcome of ['success', 'error']) {
    test(`import probe ignores late ${outcome} after ${change}`, async ({ page, center }) => {
      let pending;
      await page.route('**/api/center/v1/imports/probe', route => { pending = route; });
      await openCenter(page, center);
      await page.locator('#importButton').click();
      await page.locator('#importForm [name="root"]').fill('/fixture/a');
      await page.locator('#probeButton').click();
      await expect.poll(() => Boolean(pending)).toBe(true);
      if (change === 'path') await page.locator('#importForm [name="root"]').fill('/fixture/b');
      if (change === 'mode') await page.locator('#importForm [role="radio"][value="reference"]').check();
      if (change === 'close') await page.locator('#importDialog .dialog-close').first().click();
      if (change === 'escape') await page.keyboard.press('Escape');
      if (change === 'close' || change === 'escape') {
        await expect(page.locator('#importDialog')).not.toBeVisible();
        await page.locator('#importButton').click();
      }
      const finished = page.waitForResponse('**/api/center/v1/imports/probe');
      await pending.fulfill(outcome === 'success'
        ? { json: { schemaVersion: 1, data: { candidateId: 'old-a', candidateHash: 'hash-a', displayName: 'Old candidate A' } } }
        : { status: 400, json: { code: 'SOURCE_MISSING' } });
      await (await finished).finished();
      await page.waitForTimeout(100);
      await expect(page.locator('#probeResult')).not.toBeVisible();
      await expect(page.locator('#commitImportButton')).not.toBeVisible();
      await expect(page.locator('#importForm .form-status')).toBeEmpty();
      await expect(page.locator('#probeButton')).toBeEnabled();
    });
  }
}

test('newer import probe owns rendering and its pending button until it finishes', async ({ page, center }) => {
  const pending = [];
  await page.route('**/api/center/v1/imports/probe', route => { pending.push(route); });
  await openCenter(page, center);
  await page.locator('#importButton').click();
  const root = page.locator('#importForm [name="root"]');
  await root.fill('/fixture/a');
  await page.locator('#probeButton').click();
  await expect.poll(() => pending.length).toBe(1);
  await root.fill('/fixture/b');
  await page.locator('#probeButton').click();
  await expect.poll(() => pending.length).toBe(2);
  await pending[0].fulfill({ json: { schemaVersion: 1, data: { candidateId: 'a', candidateHash: 'hash-a', displayName: 'Old candidate A' } } });
  await page.waitForTimeout(100);
  await expect(page.locator('#probeButton')).toBeDisabled();
  await expect(page.locator('#commitImportButton')).not.toBeVisible();
  await pending[1].fulfill({ json: { schemaVersion: 1, data: { candidateId: 'b', candidateHash: 'hash-b', displayName: 'New candidate B' } } });
  await expect(page.locator('#probeResult')).toContainText('New candidate B');
  await expect(page.locator('#probeButton')).toBeEnabled();
  await expect(page.locator('#commitImportButton')).toBeVisible();
  let committed;
  await page.route('**/api/center/v1/imports/commit', route => { committed = route.request().postDataJSON(); return route.fulfill({ json: { schemaVersion: 1, data: {} } }); });
  await page.locator('#commitImportButton').click();
  await expect(page.locator('#importDialog')).not.toBeVisible();
  expect(committed.candidateId).toBe('b');
  expect(committed.candidateHash).toBe('hash-b');
});

for (const action of ['stop', 'cancel']) {
  for (const failure of ['transport', 'revision']) {
    test(`${action} keeps confirmation open after ${failure} failure`, async ({ page, center }) => {
      await queueFixture(page, center, action === 'stop');
      let release;
      const gate = new Promise(resolve => { release = resolve; });
      let calls = 0;
      await page.route(`**/api/center/v1/requests/request_fixture/${action}`, async route => {
        calls++;
        await gate;
        if (failure === 'transport') await route.abort('failed');
        else await route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ code: 'REVISION_CONFLICT' }) });
      });
      await page.locator('#queueNavButton').click();
      await page.locator('#queueContent button').filter({ hasText: action === 'stop' ? /^Stop/ : /^Cancel$/ }).click();
      await page.locator('#confirmActionButton').click();
      await expect(page.locator('#confirmActionButton')).toBeDisabled();
      await page.locator('#confirmForm').evaluate(form => form.dispatchEvent(new Event('submit', { cancelable: true })));
      await expect.poll(() => calls).toBe(1);
      release();
      await expect(page.locator('#confirmForm .form-status')).toHaveClass(/error/);
      await expect(page.locator('#confirmDialog')).toBeVisible();
      await expect(page.locator('#confirmActionButton')).toBeEnabled();
      expect(calls).toBe(1);
    });
  }
}

test('reconcile failure remains visible and repeated clicks cannot duplicate the request', async ({ page, center }) => {
  await queueFixture(page, center, true);
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  let calls = 0;
  await page.route('**/api/center/v1/requests/request_fixture/reconcile', async route => { calls++; await gate; await route.abort('failed'); });
  await page.locator('#queueNavButton').click();
  const reconcile = page.locator('[data-focus-key="request:request_fixture:reconcile"]');
  await reconcile.click();
  await expect(reconcile).toBeDisabled();
  await expect.poll(() => calls).toBe(1);
  release();
  await expect(page.locator('#actionError')).toContainText(/failed/i);
  await expect(reconcile).toBeEnabled();
  expect(calls).toBe(1);
});

for (const moveFocus of [false, true]) {
  test(`reconcile failure ${moveFocus ? 'preserves a newer focus choice' : 'restores keyboard focus to its retry control'}`, async ({ page, center }) => {
    await queueFixture(page, center, true);
    let pending;
    await page.route('**/api/center/v1/requests/request_fixture/reconcile', route => { pending = route; });
    await page.locator('#queueNavButton').click();
    const reconcile = page.locator('[data-focus-key="request:request_fixture:reconcile"]');
    await reconcile.focus(); await page.keyboard.press('Enter');
    await expect(reconcile).toBeDisabled(); await expect.poll(() => Boolean(pending)).toBe(true);
    const expectedFocus = moveFocus ? page.locator('#closeQueueButton') : reconcile;
    if (moveFocus) await expectedFocus.focus();
    await pending.fulfill({ status: 409, json: { code: 'REVISION_CONFLICT' } });
    await expect(reconcile).toBeEnabled();
    await expect(expectedFocus).toBeFocused();
  });
}

test('failed partial refresh retains last rendered freshness even after a delayed response', async ({ page, center }) => {
  await openCenter(page, center);
  const previous = await page.locator('#observedAt').textContent();
  const time = previous.match(/\d{2}:\d{2}/)?.[0];
  expect(time).toBeTruthy();
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  await page.route('**/api/center/v1/summary', async route => {
    const response = await route.fetch(); const payload = await response.json();
    payload.observedAt = '2020-01-01T00:00:00Z'; payload.revision = 999;
    await route.fulfill({ json: payload });
  });
  await page.route('**/api/center/v1/operations', route => route.abort('failed'));
  await page.route('**/api/center/v1/preferences', async route => {
    const response = await route.fetch(); const payload = await response.json();
    payload.observedAt = '2020-01-01T00:00:00Z'; payload.revision = 999;
    await gate; await route.fulfill({ json: payload });
  });
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect(page.locator('#observedAt')).toContainText(/last|stale/i);
  await expect(page.locator('#observedAt')).toContainText(time);
  release();
  await expect(page.locator('#observedAt')).toContainText(time);
  await page.locator('#queueNavButton').click();
  await expect(page.locator('#dispatchButton')).toBeDisabled();
});


test('Escape cancels only the top confirmation and restores the refreshed queue origin', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const queue = page.locator('#queueNavButton');
  await queue.focus(); await page.keyboard.press('Enter');
  const cancel = page.locator('#queueContent button').filter({ hasText: /^Cancel$/ });
  await cancel.focus(); await page.keyboard.press('Enter');
  const dialog = page.locator('#confirmDialog');
  await expect(dialog).toBeVisible();
  await page.waitForTimeout(5500);
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  await expect(page.locator('#queueDrawer')).toBeVisible();
  expect(await page.locator('#newWorkButton').evaluate(node => Boolean(node.closest('[aria-hidden="true"]')))).toBe(true);
  await expect(cancel).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(page.locator('#queueDrawer')).not.toBeVisible();
  expect(await page.locator('#newWorkButton').evaluate(node => Boolean(node.closest('[aria-hidden="true"]')))).toBe(false);
  await expect(queue).toBeFocused();
});

test('Escape from a menu confirmation returns to its More trigger', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const more = page.locator('.more-button').first();
  await more.focus(); await page.keyboard.press('Enter');
  const archive = page.getByRole('menuitem').filter({ hasText: /^Archive$/ });
  await archive.focus(); await page.keyboard.press('Enter');
  await expect(page.locator('#confirmDialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('#confirmDialog')).not.toBeVisible();
  await expect(more).toBeFocused();
  await expect(more).toHaveAttribute('aria-expanded', 'false');
});

// These delayed HTTP fixtures exercise shared Radix dialogs and real input controls.
// They never call a model or dispatch work through the fixture's fake adapter.
const preferencesFixture = { revision: 2, language: 'en', engine: 'claude', model: 'fixture-model', effort: 'high', productLanguage: 'en' };
function centerEnvelope(data) {
  return { schemaVersion: 1, centerId: 'fixture', revision: 10, observedAt: new Date().toISOString(), data };
}
async function finishDelayedResponse(page, route, options) {
  const response = page.waitForResponse(value => value.request() === route.request());
  await route.fulfill(options);
  await (await response).finished();
  // Let fetch continuations and shared dialog/focus updates reach the renderer.
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

test('settings loading disables only configuration inputs and does not steal Cancel focus', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const pending = []; let released = false;
  await page.route('**/api/center/v1/preferences', route => {
    if (!released) { pending.push(route); return; }
    return route.fulfill({ json: centerEnvelope(preferencesFixture) });
  });
  await page.locator('#settingsButton').click();
  await expect.poll(() => pending.length).toBeGreaterThan(0);
  for (const name of ['language', 'engine', 'model', 'effort', 'productLanguage']) await expect(page.locator(`#settingsForm [name="${name}"]`)).toBeDisabled();
  const close = page.locator('#settingsDialog .dialog-close').last();
  await expect(close).toBeEnabled(); await close.focus();
  released = true;
  for (const route of pending) await finishDelayedResponse(page, route, { json: centerEnvelope(preferencesFixture) });
  await expect(close).toBeFocused();
  await expect(page.locator('#settingsForm [name="model"]')).toHaveValue('fixture-model');
  for (const name of ['language', 'engine', 'model', 'effort', 'productLanguage']) await expect(page.locator(`#settingsForm [name="${name}"]`)).toBeEnabled();
  await close.click(); await expect(page.locator('#settingsDialog')).not.toBeVisible();
});

test('settings save preserves newer input and retries against its own returned revision', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const writes = [];
  await page.route('**/api/center/v1/preferences', route => {
    if (route.request().method() === 'POST') { writes.push(route); return; }
    return route.fulfill({ json: centerEnvelope(preferencesFixture) });
  });
  await page.locator('#settingsButton').click();
  const model = page.locator('#settingsForm [name="model"]'); const save = page.locator('#settingsForm [type="submit"]');
  await expect(save).toBeEnabled(); await model.fill('submitted-model'); await save.click();
  await expect.poll(() => writes.length).toBe(1);
  await model.fill('newer-unsaved-model');
  expect(writes[0].request().postDataJSON().preferences.model).toBe('submitted-model');
  await finishDelayedResponse(page, writes[0], { json: centerEnvelope({ ...preferencesFixture, model: 'submitted-model', revision: 3 }) });
  await expect(page.locator('#settingsDialog')).toBeVisible(); await expect(model).toHaveValue('newer-unsaved-model');
  await expect(page.locator('#settingsForm .form-status')).toContainText('newer edits are not saved');
  await expect(save).toBeEnabled(); await save.click(); await expect.poll(() => writes.length).toBe(2);
  expect(writes[1].request().postDataJSON()).toMatchObject({ expectedRevision: 3, preferences: { model: 'newer-unsaved-model' } });
  await finishDelayedResponse(page, writes[1], { status: 409, json: { code: 'REVISION_CONFLICT' } });
  await expect(model).toHaveValue('newer-unsaved-model'); await expect(page.locator('#settingsForm .form-status')).toHaveClass(/error/);
});

test('reopened settings hides old template controls until the new preferences load finishes', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const preferences = { ...preferencesFixture, templates: [{ templateId: 'template-old', name: 'Previous template', config: { engine: 'claude', model: 'template-model', effort: 'high', productLanguage: 'en' } }] };
  let pending; let hold = false;
  await page.route('**/api/center/v1/preferences', route => {
    if (hold) { pending = route; return; }
    return route.fulfill({ json: centerEnvelope(preferences) });
  });
  await page.locator('#settingsButton').click();
  const templates = page.locator('#settingsForm .template-controls');
  await expect(templates).toBeVisible(); await expect(templates.locator('select')).toContainText('Previous template');
  await page.locator('#settingsDialog .dialog-close').first().click(); await expect(page.locator('#settingsDialog')).not.toBeVisible();
  hold = true; await page.locator('#settingsButton').click(); await expect.poll(() => Boolean(pending)).toBe(true);
  await expect(templates).not.toBeVisible(); await expect(templates.locator('button').first()).not.toBeVisible();
  await expect(page.locator('#settingsForm [name="model"]')).toBeDisabled();
  await expect(page.locator('#settingsDialog .dialog-close').first()).toBeEnabled();
  hold = false;
  await finishDelayedResponse(page, pending, { json: centerEnvelope({ ...preferences, model: 'server-model', revision: 3 }) });
  await expect(templates).toBeVisible(); await expect(page.locator('#settingsForm [name="model"]')).toHaveValue('server-model');
});

for (const kind of ['continue', 'new']) {
  test(`${kind} work completion preserves a reopened form and does not open the queue over it`, async ({ page, center }) => {
    const { entry } = await queueFixture(page, center, false);
    const formId = kind === 'continue' ? 'continue' : 'newWork';
    const openWork = async () => {
      if (kind === 'continue') {
        await page.locator('.more-button').first().click();
        await page.getByRole('menuitem', { name: 'Continue', exact: true }).click();
      } else await page.locator('#newWorkButton').click();
    };
    const marker = `Catalog reconciled after ${kind} work`;
    const refreshReads = []; let refreshReleased = false; let pending;
    // Hold the final read in any in-flight refresh. The completed write must
    // reach its global success status before we let that snapshot render.
    await page.route('**/api/center/v1/preferences', route => {
      if (!refreshReleased) { refreshReads.push(route); return; }
      return route.fulfill({ json: centerEnvelope(preferencesFixture) });
    });
    await page.route('**/api/center/v1/entries?*', route => route.fulfill({ json: centerEnvelope({
      items: [{ ...entry, displayName: marker }], total: 1, nextCursor: null,
    }) }));
    await page.route(`**/api/center/v1/${kind === 'continue' ? 'requests' : 'explorations/batch'}`, route => { pending = route; });
    await openWork(); await page.locator(`#${formId}Form [type="submit"]`).click();
    await expect.poll(() => Boolean(pending)).toBe(true);
    await page.locator(`#${formId}Dialog .dialog-close`).first().click();
    await expect(page.locator(`#${formId}Dialog`)).not.toBeVisible(); await openWork();
    const model = page.locator(`#${formId}Form [name="model"]`); await model.fill('new-form-model');
    await finishDelayedResponse(page, pending, { json: centerEnvelope({}) });
    await expect(page.locator('[data-sonner-toast]').last()).toBeVisible();
    await expect.poll(() => refreshReads.length).toBeGreaterThan(0);
    refreshReleased = true;
    for (const route of refreshReads) await finishDelayedResponse(page, route, { json: centerEnvelope(preferencesFixture) });
    // Unlike observing a GET, this marker proves the full refresh reached
    // renderPage, after which the awaiting work handler decides on openQueue.
    await expect(page.locator('#productRows')).toContainText(marker);
    await expect(page.locator(`#${formId}Dialog`)).toBeVisible(); await expect(model).toHaveValue('new-form-model');
    await expect(model).toBeFocused(); await expect(page.locator(`#${formId}Form [type="submit"]`)).toBeEnabled();
    await expect(page.locator('#queueDrawer')).not.toBeVisible();
  });
}

test('old cancel failure cannot overwrite or unlock a newer stop-all confirmation', async ({ page, center }) => {
  await queueFixture(page, center, false);
  let old; let current;
  await page.route('**/api/center/v1/requests/request_fixture/cancel', route => { old = route; });
  await page.route('**/api/center/v1/queue/stop-all', route => { current = route; });
  await page.locator('#queueNavButton').click();
  await page.locator('#queueContent button').filter({ hasText: /^Cancel$/ }).click(); await page.locator('#confirmActionButton').click();
  await expect.poll(() => Boolean(old)).toBe(true);
  await page.locator('#confirmDialog .dialog-close').first().click(); await page.locator('#stopAllButton').click();
  await expect(page.locator('#confirmActionButton')).toBeEnabled(); await page.locator('#confirmActionButton').click();
  await expect.poll(() => Boolean(current)).toBe(true);
  await finishDelayedResponse(page, old, { status: 409, json: { code: 'REVISION_CONFLICT' } });
  await expect(page.locator('#confirmDialog')).toBeVisible(); await expect(page.locator('#confirmActionButton')).toBeDisabled();
  await expect(page.locator('#confirmForm .form-status')).toContainText('Submitting…');
  await finishDelayedResponse(page, current, { json: centerEnvelope({}) });
  await expect(page.locator('#confirmDialog')).not.toBeVisible();
});

test('old import commit preserves the next candidate and its pending confirmation', async ({ page, center }) => {
  await queueFixture(page, center, false);
  let probes = 0; const commits = [];
  await page.route('**/api/center/v1/imports/probe', route => {
    const id = ++probes;
    return route.fulfill({ json: centerEnvelope({ candidateId: `candidate-${id}`, candidateHash: `hash-${id}`, displayName: `Candidate ${id}` }) });
  });
  await page.route('**/api/center/v1/imports/commit', route => { commits.push(route); });
  await page.locator('#importButton').click(); await page.locator('#importForm [name="root"]').fill('/fixture/a');
  await page.locator('#probeButton').click(); await expect(page.locator('#probeResult')).toContainText('Candidate 1');
  await page.locator('#commitImportButton').click(); await expect.poll(() => commits.length).toBe(1);
  await page.locator('#importDialog .dialog-close').first().click(); await page.locator('#importButton').click();
  await page.locator('#importForm [name="root"]').fill('/fixture/b'); await page.locator('#probeButton').click();
  await expect(page.locator('#probeResult')).toContainText('Candidate 2'); await page.locator('#commitImportButton').click();
  await expect.poll(() => commits.length).toBe(2);
  expect(commits[1].request().postDataJSON()).toMatchObject({ candidateId: 'candidate-2', candidateHash: 'hash-2' });
  await finishDelayedResponse(page, commits[0], { json: centerEnvelope({}) });
  await expect(page.locator('#importDialog')).toBeVisible(); await expect(page.locator('#probeResult')).toContainText('Candidate 2');
  await expect(page.locator('#commitImportButton')).toBeDisabled(); await expect(page.locator('#importForm .form-status')).toContainText('Submitting…');
  await finishDelayedResponse(page, commits[1], { json: centerEnvelope({}) });
  await expect(page.locator('#importDialog')).not.toBeVisible();
});

test('source selection keeps its current fields when an older takeover fails', async ({ page, center }) => {
  await queueFixture(page, center, false);
  const sources = ['source-a', 'source-b'].map(sourceId => ({ sourceId, kind: 'runtime', revision: 1, displayName: sourceId, availability: 'available' }));
  await page.route(`**/api/center/v1/entries/${center.entryId}`, route => route.fulfill({ json: centerEnvelope({
    entryId: center.entryId, displayName: 'Queue fixture', sourceId: 'source-a', revision: 1, sources, capabilities: { takeover: true },
  }) }));
  let pending;
  await page.route('**/api/center/v1/sources/source-a/takeover', route => { pending = route; });
  await page.locator('.more-button').first().click(); await page.getByRole('menuitem').filter({ hasText: /^Manage sources$/ }).click();
  await page.locator('#sourceManagerBody button').filter({ hasText: /^Take over with center$/ }).click(); await expect.poll(() => Boolean(pending)).toBe(true);
  const selected = page.locator('#sourceManagerBody [role="radio"][value="source-b"]'); await selected.check();
  const root = page.locator('#sourceManagerBody .reconnect-field input'); await root.fill('/fixture/new-source');
  const status = await page.locator('#sourceManagerStatus').textContent();
  await finishDelayedResponse(page, pending, { status: 409, json: { code: 'SOURCE_CHANGED' } });
  await expect(selected).toBeChecked(); await expect(root).toHaveValue('/fixture/new-source'); await expect(root).toBeFocused();
  await expect(page.locator('#sourceManagerStatus')).toHaveText(status);
});

for (const failure of [false, true]) {
  test(`source switch keeps the serial action lock visible until old ${failure ? 'failure' : 'success'} finishes`, async ({ page, center }) => {
    await queueFixture(page, center, false);
    const sources = ['source-a', 'source-b'].map(sourceId => ({ sourceId, kind: 'runtime', revision: 1, displayName: sourceId, availability: 'available' }));
    let selected = false; let pending; const selections = [];
    await page.route(`**/api/center/v1/entries/${center.entryId}`, route => route.fulfill({ json: centerEnvelope({
      entryId: center.entryId, sourceId: selected ? 'source-b' : 'source-a', revision: 1, sources, capabilities: { takeover: true },
    }) }));
    await page.route('**/api/center/v1/sources/source-a/takeover', route => { pending = route; });
    await page.route(`**/api/center/v1/entries/${center.entryId}/source-selection`, route => {
      selections.push(route.request().postDataJSON()); selected = true; return route.fulfill({ json: centerEnvelope({}) });
    });
    await page.locator('.more-button').first().click(); await page.getByRole('menuitem', { name: 'Manage sources', exact: true }).click();
    const takeover = page.locator('#sourceManagerBody button').filter({ hasText: /^Take over with center$/ });
    await takeover.click(); await expect.poll(() => Boolean(pending)).toBe(true);
    const sourceB = page.locator('#sourceManagerBody [role="radio"][value="source-b"]'); await sourceB.check();
    const useB = page.locator('#sourceManagerBody button').filter({ hasText: /^Use selected source$/ });
    await expect(useB).toBeDisabled(); await expect(useB.locator('..')).toContainText('Operation in progress');
    const root = page.locator('#sourceManagerBody .reconnect-field input'); await root.fill('/fixture/b-draft');
    await finishDelayedResponse(page, pending, failure ? { status: 409, json: { code: 'SOURCE_CHANGED' } } : { json: centerEnvelope({ state: 'succeeded' }) });
    await expect(useB).toBeEnabled(); await expect(takeover).toBeDisabled(); await expect(sourceB).toBeChecked();
    await expect(root).toHaveValue('/fixture/b-draft'); await expect(root).toBeFocused();
    await expect(page.locator('#sourceManagerStatus')).toBeEmpty(); expect(selections).toEqual([]);
    await useB.click(); await expect.poll(() => selections.length).toBe(1);
    expect(selections[0].sourceId).toBe('source-b'); await expect(page.locator('#sourceManagerStatus')).toHaveText('Current source updated.');
  });
}

test('closing confirmation falls back inside the queue when its original action disappears', async ({ page, center }) => {
  await queueFixture(page, center, false);
  await page.locator('#queueNavButton').click();
  const cancel = page.locator('#queueContent button').filter({ hasText: /^Cancel$/ }); await cancel.click();
  await expect(page.locator('#confirmDialog')).toBeVisible();
  await page.route('**/api/center/v1/requests?*', route => route.fulfill({ json: centerEnvelope({ items: [], revision: 2 }) }));
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect(cancel).toHaveCount(0);
  await page.keyboard.press('Escape'); await expect(page.locator('#confirmDialog')).not.toBeVisible();
  await expect(page.locator('#queueDrawer')).toBeVisible(); await expect(page.locator('#closeQueueButton')).toBeFocused();
});

for (const change of ['hidden', 'disabled', 'drawer-closed']) {
  test(`confirmation focus ignores its ${change} origin`, async ({ page, center }) => {
    await queueFixture(page, center, false);
    await page.locator('#queueNavButton').click();
    const cancel = page.locator('#queueContent button').filter({ hasText: /^Cancel$/ });
    await cancel.click(); await expect(page.locator('#confirmDialog')).toBeVisible();
    if (change === 'drawer-closed') await page.evaluate(() => document.getElementById('queueDrawer').close());
    else await cancel.evaluate((node, mode) => { if (mode === 'hidden') node.hidden = true; else node.disabled = true; }, change);
    await page.keyboard.press('Escape'); await expect(page.locator('#confirmDialog')).not.toBeVisible();
    await expect(page.locator(change === 'drawer-closed' ? '#queueNavButton' : '#closeQueueButton')).toBeFocused();
  });
}

test('reconnect failure keeps retry focus and clears its error after the path changes', async ({ page, center }) => {
  await queueFixture(page, center, false);
  await page.route(`**/api/center/v1/entries/${center.entryId}`, route => route.fulfill({ json: centerEnvelope({
    entryId: center.entryId, sourceId: 'source-a', revision: 1, sources: [{ sourceId: 'source-a', kind: 'runtime', revision: 1, availability: 'available' }], capabilities: {},
  }) }));
  await page.route('**/api/center/v1/imports/probe', route => route.fulfill({ status: 409, json: { code: 'SOURCE_CHANGED' } }));
  await page.locator('.more-button').first().click(); await page.getByRole('menuitem', { name: 'Manage sources', exact: true }).click();
  const root = page.locator('#sourceManagerBody .reconnect-field input'); await root.fill('/fixture/old');
  const reconnect = page.locator('#sourceManagerBody button').filter({ hasText: /^Reconnect/ });
  await reconnect.focus(); await page.keyboard.press('Enter');
  await expect(page.locator('#sourceManagerStatus')).toHaveClass(/error/);
  await expect(reconnect).toBeEnabled(); await expect(reconnect).toBeFocused();
  await root.fill('/fixture/new'); await expect(page.locator('#sourceManagerStatus')).toBeEmpty();
});
