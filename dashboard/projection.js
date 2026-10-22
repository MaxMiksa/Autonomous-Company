/* Versioned read acceptance. Only a current core read can confirm a new epoch. */
(() => {
  'use strict';
  const scopeKey = data => JSON.stringify([data?.centerId, data?.entryId, data?.sourceId,
    data?.sourceBindingVersion, data?.productId ?? null, data?.explorationId ?? null]);
  const version = value => Number.isSafeInteger(value) && value >= 0;
  const ordered = value => Array.isArray(value) ? value.map(ordered) : value && typeof value === 'object'
    ? Object.fromEntries(Object.keys(value).sort().map(key => [key, ordered(value[key])])) : value;
  const fingerprint = value => JSON.stringify(ordered(value));
  function coreFacts(data) {
    return {
      currentCycleId: data.currentCycleId,
      runtime: Object.fromEntries(['state', 'processState', 'currentCycleId', 'active', 'pauseReason'].map(key => [key, data.runtime?.[key]])),
      cycles: (data.cycles || []).map(cycle => ({ id: cycle.id, sequenceNumber: cycle.sequenceNumber,
        protocolState: cycle.protocolState, outcome: cycle.outcome, status: cycle.status, active: cycle.active,
        objective: cycle.objective, workKind: cycle.workKind, activeAttemptId: cycle.activeAttemptId,
        attempts: (cycle.attempts || []).map(attempt => ({ attemptId: attempt.attemptId, status: attempt.status,
          writersStopped: attempt.writersStopped, startedAt: attempt.startedAt, endedAt: attempt.endedAt })),
        qualityApplicability: cycle.qualityApplicability,
        continuationDecision: cycle.continuationDecision && Object.fromEntries(Object.entries(cycle.continuationDecision)
          .filter(([key]) => !['checkedAt', 'observedAt', 'confirmedAt'].includes(key))),
      })),
    };
  }
  class Gate {
    constructor() { this.generation = 0; this.scope = null; this.epoch = null; this.revision = null; this.facts = null; this.parts = new Map(); }
    ticket() { return { generation: this.generation, scope: this.scope, epoch: this.epoch }; }
    matches(data) { return data?.projectionVersion === 2 && scopeKey(data) === this.scope && data.projectionEpoch === this.epoch; }
    core(data) {
      if (data?.projectionVersion !== 2 || !data.centerId || !data.entryId || !data.sourceId
        || !data.sourceBindingVersion || !data.projectionEpoch || !(data.snapshotRevision === null || version(data.snapshotRevision))) throw new Error('Invalid core projection');
      const key = scopeKey(data);
      const reset = key !== this.scope || data.projectionEpoch !== this.epoch;
      const facts = fingerprint(coreFacts(data));
      if (!reset && version(this.revision)) {
        if (!version(data.snapshotRevision) || data.snapshotRevision < this.revision) throw new Error('Stale core projection');
        if (data.snapshotRevision === this.revision && facts !== this.facts) throw new Error('Conflicting core projection');
      }
      if (reset) { this.generation += 1; this.parts.clear(); }
      this.scope = key; this.epoch = data.projectionEpoch; this.revision = data.snapshotRevision; this.facts = facts;
      return reset;
    }
    component(key, value, metadata, data, ticket = this.ticket()) {
      if (ticket.generation !== this.generation || ticket.scope !== this.scope || ticket.epoch !== this.epoch || !this.matches(data)) return false;
      const revision = metadata?.revision ?? null;
      if (revision !== null && !version(revision)) return false;
      const previous = this.parts.get(key), facts = fingerprint(value);
      if (previous && version(previous.revision)) {
        if (!version(revision) || revision < previous.revision || revision === previous.revision && facts !== previous.facts) return false;
      }
      this.parts.set(key, { revision, facts });
      return true;
    }
  }
  window.DashboardProjection = Object.freeze({ Gate, scopeKey, coreFacts });
})();
