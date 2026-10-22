import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dashboard'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/core'))
from harness_projection import legacy_cycle, project_cycles, protocol_cycle
from company_harness import HarnessStore


class HarnessProjectionTests(unittest.TestCase):
    def test_legacy_mapping_preserves_failure_numbering_and_report_meaning(self):
        row = {'id': 'old-cycle', 'sequenceNumber': 27, 'status': 'failed',
               'workReport': {'phase': 'review', 'final': True}, 'usage': None,
               'events': [{'sequence': 1}], 'startedAt': '2026-10-21T23:59:00Z'}
        original = copy.deepcopy(row)
        value = legacy_cycle(row)
        self.assertEqual(row, original)
        self.assertEqual(value['sequenceNumber'], 27)
        self.assertEqual(value['status'], 'failed')
        self.assertIsNone(value['outcome'])
        self.assertEqual(value['qualityApplicability'], [])
        self.assertFalse(value['continuationDecision']['allowed'])
        self.assertEqual(value['attempts'][0]['attemptId'], 'legacy:old-cycle')
        self.assertIsNone(value['attempts'][0]['usage'])
        value['attempts'][0]['events'].append({'sequence': 2})
        self.assertEqual(row, original)

    def test_two_attempts_do_not_add_business_rows_or_reuse_old_report(self):
        logical = {'cycleId': 'same', 'productId': 'p', 'sequenceNumber': 8, 'protocolState': 'correcting',
                   'activeAttemptId': 'a2', 'attempts': [
                       {'attemptId': 'a1', 'status': 'failed', 'events': [{'sequence': 1}]},
                       {'attemptId': 'a2', 'status': 'running', 'events': [{'sequence': 1}]}],
                   'report': {'status': 'missing'}}
        old = {'id': 'same', 'stableProductId': 'p', 'sequenceNumber': 8, 'report': 'old text',
               'workReport': {'title': 'Previous attempt'}, 'summary': 'old text'}
        values = project_cycles([old], {'cycles': [logical]})
        self.assertEqual(len(values), 1)
        value = values[0]
        self.assertEqual(value['sequenceNumber'], 8)
        self.assertEqual(value['status'], 'correcting')
        self.assertEqual(len(value['attempts']), 2)
        self.assertIsNone(value['workReport'])
        self.assertEqual(value['summary'], '')
        self.assertEqual([event['sequence'] for event in value['events']], [1])
        self.assertEqual(value['events'][0]['attemptId'], 'a2')
        self.assertNotIn('currentCycle', value)

    def test_closed_is_not_automatically_success_or_quality_approval(self):
        for outcome, expected in [('failed', 'failed'), ('partial', 'handoff'),
                                  ('blocked', 'blocked'), (None, 'unknown'),
                                  ('completed', 'completed')]:
            with self.subTest(outcome=outcome):
                value = protocol_cycle({'cycleId': 'c', 'protocolState': 'closed', 'outcome': outcome,
                                        'report': {'status': 'available', 'title': 'Draft',
                                                   'summary': 'Ready for review', 'reportedPhase': 'review'}})
                self.assertEqual(value['status'], expected)
                self.assertFalse(value['active'])
                self.assertFalse(value['continuationDecision']['allowed'])
                self.assertEqual(value['qualityApplicability'], [])
                self.assertEqual(value['workReport']['phase'], 'review')

    def test_unknown_time_is_not_made_reliable_or_renumbered(self):
        value = protocol_cycle({'cycleId': 'new', 'protocolState': 'attention',
                                'time': {'executionSeconds': None, 'totalSeconds': None,
                                         'reliability': 'unknown'}})
        self.assertFalse(value['elapsedReliable'])
        self.assertIsNone(value['elapsedSeconds'])
        self.assertNotIn('sequenceNumber', value)
        self.assertEqual(value['status'], 'unknown')

    def test_unrecorded_cycles_require_explicit_matching_identity_scope(self):
        snapshot = {'cycles': [{'cycleId': 'mine', 'productId': 'p1'},
                               {'cycleId': 'other', 'productId': 'p2'}]}
        self.assertEqual(project_cycles([], snapshot), [])
        scoped = project_cycles([], snapshot, {'productId': 'p1'})
        self.assertEqual([row['id'] for row in scoped], ['mine'])

    def test_closed_attempt_keeps_real_events_without_claiming_a_live_writer(self):
        value = protocol_cycle({'cycleId': 'c', 'protocolState': 'closed', 'outcome': 'failed',
                                'attempts': [{'attemptId': 'a', 'status': 'ended',
                                              'events': [{'sequence': 2, 'observedAt': '2026-10-22T12:00:00Z',
                                                          'event': {'kind': 'process.exited'}}]}]})
        self.assertFalse(value['active'])
        self.assertEqual(value['events'][0]['kind'], 'process.exited')
        self.assertEqual(value['events'][0]['attemptId'], 'a')

    def test_overlay_rejects_ownership_conflict_before_replacing_old_data(self):
        row = {'id': 'c', 'stableProductId': 'p1', 'status': 'failed'}
        snapshot = {'cycles': [{'cycleId': 'c', 'productId': 'p2'}]}
        with self.assertRaisesRegex(ValueError, 'ownership conflicts'):
            project_cycles([row], snapshot, {'productId': 'p1'})
        self.assertEqual(row['stableProductId'], 'p1')

    def test_exploration_scope_does_not_include_descendant_product_cycles(self):
        snapshot = {'cycles': [{'cycleId': 'explore', 'explorationId': 'e'},
                               {'cycleId': 'product', 'productId': 'p', 'explorationId': 'e'}]}
        self.assertEqual([row['id'] for row in project_cycles([], snapshot, {'explorationId': 'e'})], ['explore'])
        self.assertEqual([row['id'] for row in project_cycles([], snapshot, {'productId': 'p', 'explorationId': 'e'})], ['product'])
        self.assertEqual([row['id'] for row in project_cycles([], snapshot, {
            'productId': 'p', 'explorationId': 'e', 'includeExploration': True})], ['explore', 'product'])

    def test_cycle_metering_replaces_stale_single_attempt_amounts(self):
        usage = {'cost': 5, 'costComplete': True, 'inputTokens': 30, 'outputTokens': 7,
                 'totalTokens': 37, 'status': 'available', 'coverage': {'scope': 'cycle'}}
        value = protocol_cycle({'cycleId': 'c', 'usage': usage},
                               {'id': 'c', 'costUsd': 2, 'usage': {'totalTokens': 11}})
        self.assertEqual(value['costUsd'], 5)
        self.assertEqual(value['usage']['totalTokens'], 37)
        self.assertEqual(value['costStatus'], 'reported')
        missing = protocol_cycle({'cycleId': 'c'}, {'costUsd': 2, 'usage': {'totalTokens': 11}})
        self.assertIsNone(missing['costUsd'])
        self.assertIsNone(missing['usage']['totalTokens'])
        self.assertEqual(missing['usage']['status'], 'partial')

    def test_model_report_does_not_interpret_an_extra_value_wrapper(self):
        value = protocol_cycle({'cycleId': 'c', 'report': {'summary': 'Real summary',
            'title': 'Real title', 'reportedPhase': 'planning', 'value': {'summary': 'x' * 1000}}})
        self.assertEqual(value['summary'], 'Real summary')

    def test_actual_store_two_attempt_costs_project_as_one_settled_cycle(self):
        with tempfile.TemporaryDirectory() as root:
            store = HarnessStore(root, create=True)
            store.create_cycle({'cycleId': 'c', 'productId': 'p', 'sequenceNumber': 9,
                                'objective': 'Review definition', 'workKind': 'review'})
            for attempt, cost in [('a1', 2), ('a2', 3)]:
                context = store.begin_attempt('c', attempt, {'dispatchId': 'test-owned'})['context']
                store.record_usage('c', attempt, {'callId': attempt, 'coverage': 'self',
                                                'cost': cost, 'inputTokens': cost, 'outputTokens': 1})
                store.finish_attempt(context, {'outcome': 'failed', 'exitCode': 1},
                                     writers_stopped=True, observation={'executionTree': 'verified-terminated'})
                store.confirm_usage('c', attempt, [attempt], source='fixture_provider',
                                    observation={'callSet': 'complete'})
            store.close_cycle('c', 'close', outcome='failed', verification={
                'writersStopped': True, 'attemptResults': ['a1', 'a2'], 'evidenceRefs': [],
                'checkedAt': '2026-10-22T12:00:00+00:00'})
            rows = project_cycles([{'id': 'c', 'stableProductId': 'p', 'costUsd': 2,
                                    'usage': {'totalTokens': 3}}], store.snapshot(), {'productId': 'p'})
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['costUsd'], 5)
            self.assertEqual(rows[0]['usage']['totalTokens'], 7)
            self.assertTrue(rows[0]['usage']['costComplete'])
            self.assertEqual(rows[0]['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
