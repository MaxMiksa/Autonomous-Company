import { test as base, expect } from '@playwright/test';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';

export { expect };

export const test = base.extend({
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
