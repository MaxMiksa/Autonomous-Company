const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

function fixture() {
  const context = vm.createContext({ window: {} });
  vm.runInContext(fs.readFileSync(path.join(__dirname, '../dashboard/projection.js'), 'utf8'), context);
  const data = { projectionVersion: 2, centerId: 'center', entryId: 'entry', sourceId: 'source',
    sourceBindingVersion: 'binding', productId: 'product', explorationId: null,
    projectionEpoch: 'epoch', snapshotRevision: 4, currentCycleId: 'c2',
    runtime: { state: 'running', processState: 'running', currentCycleId: 'c2' },
    cycles: [{ id: 'c2', status: 'correcting', protocolState: 'correcting', activeAttemptId: 'a2',
      attempts: [{ attemptId: 'a1', status: 'exited' }, { attemptId: 'a2', status: 'running' }] }] };
  return { gate: new context.window.DashboardProjection.Gate(), data, context };
}

test('same core facts permit elapsed time, freshness and independent component updates', () => {
  const { gate, data } = fixture();
  assert.equal(gate.core(data), true);
  assert.equal(gate.component('usage:all', { total: 5 }, { revision: 1 }, data), true);
  const next = { ...data, sourceRevision: 99, generatedAt: 'later', runtime: { ...data.runtime, elapsedSeconds: 100 },
    cycles: data.cycles.map(cycle => ({ ...cycle, time: { totalSeconds: 100 }, report: 'New report' })) };
  assert.equal(gate.core(next), false);
  assert.equal(gate.component('usage:all', { total: 8 }, { revision: 2, freshness: 'fresh' }, next), true);
  assert.equal(gate.component('usage:all', { total: 8 }, { revision: 2, freshness: 'stale', asOf: 'later' }, next), true);
});

test('stale or conflicting facts reject only their own component', () => {
  const { gate, data } = fixture(); gate.core(data);
  gate.component('media', { image: 'first' }, { revision: 3 }, data);
  assert.equal(gate.component('media', { image: 'old' }, { revision: 2 }, data), false);
  assert.equal(gate.component('media', { image: 'conflict' }, { revision: 3 }, data), false);
  assert.equal(gate.component('report:c2:a2', { summary: 'Current attempt' }, { revision: 8 }, data), true);
  assert.equal(gate.core({ ...data, snapshotRevision: 5, currentCycleId: 'c3' }), false);
  assert.equal(gate.revision, 5);
});

test('only core confirms epochs and invalidates all prior component requests', () => {
  const { gate, data } = fixture(); gate.core(data);
  const ticket = gate.ticket();
  const future = { ...data, projectionEpoch: 'new', snapshotRevision: 0 };
  assert.equal(gate.component('media', {}, { revision: 1 }, future, ticket), false);
  assert.equal(gate.epoch, 'epoch');
  assert.equal(gate.core(future), true);
  assert.equal(gate.component('media', {}, { revision: 10 }, data, ticket), false);
  assert.equal(gate.component('media', {}, { revision: 1 }, future, ticket), false);
  assert.equal(gate.epoch, 'new');
});

test('real binding changes invalidate old reads while ordinary source revision does not', () => {
  const { gate, data } = fixture(); gate.core(data);
  const ticket = gate.ticket();
  gate.core({ ...data, sourceRevision: 10 });
  assert.equal(gate.component('history:cursor', ['c1'], { revision: 1 }, data, ticket), true);
  gate.core({ ...data, sourceBindingVersion: 'rebound' });
  assert.equal(gate.component('history:cursor', ['c1'], { revision: 2 }, data, ticket), false);
});

test('unknown component ordering never overwrites reliable facts or advances core', () => {
  const { gate, data } = fixture(); gate.core(data);
  assert.equal(gate.component('usage', { total: null }, { revision: null }, data), true);
  assert.equal(gate.component('usage', { total: 5 }, { revision: 2 }, data), true);
  assert.equal(gate.component('usage', { total: null }, { revision: null }, data), false);
  assert.throws(() => gate.core({ ...data, snapshotRevision: 3 }), /Stale/);
  assert.throws(() => gate.core({ ...data, currentCycleId: 'wrong' }), /Conflicting/);
  assert.equal(gate.revision, 4);
});

test('a newer unavailable check establishes a floor against delayed empty detail', () => {
  const { gate, data, context } = fixture();
  context.projection = gate;
  const app = fs.readFileSync(path.join(__dirname, '../dashboard/app.js'), 'utf8');
  vm.runInContext(app.slice(app.indexOf('  function installCycleComponents('), app.indexOf('  function retainHistoricalCycles(')), context);
  const original = { ...data, cycles: [{ ...data.cycles[0], checks: [], latestCheck: null, checkStatus: 'unregistered',
    partitions: { checks: { status: 'missing', revision: 1 } } }] };
  gate.core(original);
  context.installCycleComponents(original);
  const current = { ...original, snapshotRevision: 5, cycles: [{ ...original.cycles[0], executionIssue: { code: 'COLLECTION_UNCONFIRMED' },
    partitions: { checks: { status: 'unavailable', revision: 2, errorCode: 'COLLECTION_UNCONFIRMED' } } }] };
  gate.core(current);
  context.installCycleComponents(current, original);
  const delayed = { ...original, cycles: [{ ...original.cycles[0], partitions: { checks: { status: 'missing', revision: 1 } } }] };
  context.installCycleComponents(delayed, current);
  assert.equal(delayed.cycles[0].partitions.checks.status, 'unavailable');
  assert.equal(gate.component('usage:c2:a2', { total: 12 }, { revision: 3 }, original), true);
  const recovered = { ...current, cycles: [{ ...current.cycles[0], checks: [], latestCheck: null,
    partitions: { checks: { status: 'missing', revision: 3 } } }] };
  context.installCycleComponents(recovered, current);
  assert.equal(recovered.cycles[0].partitions.checks.status, 'missing');
});
