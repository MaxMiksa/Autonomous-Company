"""Quality bindings and dispatch prerequisites, without invoking a model."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/core'))
from company_harness import HarnessError
from company_harness_quality import close_review, prepare_contract


class MemoryEvidence:
    def __init__(self):
        self.cycles, self.evidence = [], {}

    def snapshot(self):
        return {'cycles': copy.deepcopy(self.cycles)}

    def read_evidence(self, identity):
        return copy.deepcopy(self.evidence.get(identity))

    def artifact(self, identity, kind, *, product='p', exploration=None):
        ref = {'evidenceId': identity + '-doc', 'sha256': identity[0] * 64}
        attempt = identity + '-author'
        submission = {'submissionId': identity + '-submit', 'attemptId': attempt,
                      'payload': {'result': 'completed', 'evidenceRefs': [ref]}}
        cycle = {'cycleId': identity, 'productId': product, 'explorationId': exploration,
                 'protocolState': 'closed', 'outcome': 'completed', 'activeAttemptId': None,
                 'contract': {'workKind': kind, 'artifactKind': kind},
                 'attempts': [{'attemptId': attempt, 'writersStopped': True}],
                 'submissions': [submission], 'qualityApplicability': []}
        self.cycles.append(cycle)
        self.evidence[ref['evidenceId']] = {**ref, 'cycleId': identity,
                                           'source': {'attemptId': attempt}, 'content': 'Actual material'}
        return ref, cycle, submission

    def reviewed(self, target, allowed, *, verdict='passed'):
        ref, cycle, submission = self.artifact('r' + str(len(self.cycles)), 'review')
        cycle['contract']['inputRefs'] = [target]
        submission['payload']['review'] = {'targetRefs': [target], 'verdict': verdict,
                                           'issues': [], 'qualityApplicability': allowed}
        cycle['qualityApplicability'] = close_review(self, cycle, submission)
        return ref, cycle


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryEvidence()

    def proposal(self, kind, inputs=None, prereqs=None, **kwargs):
        return {'objective': 'One outcome', 'workKind': kind, 'scope': ['one task'],
                'completionOrHandoff': 'Readable outcome', 'inputRefs': inputs or [],
                'prerequisiteRefs': prereqs or [], **kwargs}

    def test_definition_requires_real_direction_and_independent_review(self):
        with self.assertRaisesRegex(HarnessError, 'PREREQUISITE_MISSING'):
            prepare_contract(self.store, self.proposal('definition'), {'productId': 'p'})
        direction, _, _ = self.store.artifact('d1', 'direction')
        with self.assertRaisesRegex(HarnessError, 'REVIEW_REQUIRED'):
            prepare_contract(self.store, self.proposal('definition', [direction]), {'productId': 'p'})
        review, _ = self.store.reviewed(direction, ['definition'])
        value = prepare_contract(self.store, self.proposal('definition', [direction], [review]), {'productId': 'p'})
        self.assertEqual(value['artifactKind'], 'definition')
        self.assertNotIn('continuationDecision', value)

    def test_invalid_enum_shapes_return_repairable_protocol_errors(self):
        for field, value in [('workKind', []), ('timeClass', {}), ('revisesKind', [])]:
            with self.subTest(field=field):
                proposal = self.proposal('revision' if field == 'revisesKind' else 'research')
                proposal[field] = value
                with self.assertRaises(HarnessError) as caught:
                    prepare_contract(self.store, proposal, {'productId': 'p'})
                self.assertEqual(caught.exception.code, 'INVALID_FIELD')
                self.assertEqual(caught.exception.field, field)
        target, _, _ = self.store.artifact('d1', 'definition')
        _, reviewer, submission = self.store.artifact('r1', 'review')
        reviewer['contract']['inputRefs'] = [target]
        submission['payload']['review'] = {'targetRefs': [target], 'verdict': [],
                                           'issues': [], 'qualityApplicability': ['visual_exploration']}
        with self.assertRaises(HarnessError) as caught:
            close_review(self.store, reviewer, submission)
        self.assertEqual(caught.exception.code, 'INVALID_REVIEW')
        self.assertEqual(caught.exception.field, 'verdict')
        submission['payload']['review'].update(verdict='passed', issues=[{'blocking': 1}])
        with self.assertRaises(HarnessError) as caught:
            close_review(self.store, reviewer, submission)
        self.assertEqual(caught.exception.code, 'INVALID_REVIEW')
        self.assertEqual(caught.exception.field, 'issues')

    def test_implementation_cannot_omit_prototype_even_with_definition_review(self):
        definition, _, _ = self.store.artifact('d1', 'definition')
        review, _ = self.store.reviewed(definition, ['implementation'])
        with self.assertRaisesRegex(HarnessError, 'PREREQUISITE_MISSING'):
            prepare_contract(self.store, self.proposal('implementation', [definition], [review]), {'productId': 'p'})

    def test_new_head_cannot_use_old_version_review(self):
        old, _, _ = self.store.artifact('d1', 'definition')
        review, _ = self.store.reviewed(old, ['visual_exploration'])
        newer, _, _ = self.store.artifact('d2', 'definition')
        with self.assertRaisesRegex(HarnessError, 'PREREQUISITE_MISSING'):
            prepare_contract(self.store, self.proposal('visual_exploration', [old], [review]), {'productId': 'p'})
        with self.assertRaisesRegex(HarnessError, 'REVIEW_REQUIRED'):
            prepare_contract(self.store, self.proposal('visual_exploration', [newer], [review]), {'productId': 'p'})

    def test_model_identity_and_foreign_product_evidence_do_not_authorize(self):
        foreign, _, _ = self.store.artifact('d1', 'definition', product='other')
        with self.assertRaisesRegex(HarnessError, 'OWNER_MISMATCH'):
            prepare_contract(self.store, self.proposal('review', [foreign]), {'productId': 'p'})
        value = prepare_contract(self.store, self.proposal('research', productId='other'), {'productId': 'p'})
        self.assertNotIn('productId', value)

    def test_same_author_attempt_and_wrong_target_are_rejected(self):
        target, producer, _ = self.store.artifact('d1', 'definition')
        _, reviewer, submission = self.store.artifact('r1', 'review')
        reviewer['contract']['inputRefs'] = [target]
        submission['payload']['review'] = {'targetRefs': [target], 'verdict': 'passed',
                                           'issues': [], 'qualityApplicability': ['visual_exploration']}
        self.store.evidence[target['evidenceId']]['source']['attemptId'] = submission['attemptId']
        with self.assertRaisesRegex(HarnessError, 'REVIEW_INDEPENDENCE_UNCONFIRMED'):
            close_review(self.store, reviewer, submission)
        self.store.evidence[target['evidenceId']]['source']['attemptId'] = producer['attempts'][0]['attemptId']
        submission['payload']['review']['targetRefs'] = []
        with self.assertRaisesRegex(HarnessError, 'INVALID_REVIEW'):
            close_review(self.store, reviewer, submission)

    def test_pending_review_is_precheck_only_until_persisted_closed(self):
        direction, _, _ = self.store.artifact('d1', 'direction')
        review, cycle = self.store.reviewed(direction, ['definition'])
        quality = cycle['qualityApplicability']
        cycle.update(protocolState='validating', outcome=None, qualityApplicability=[])
        proposal = self.proposal('definition', [direction], [review])
        with self.assertRaises(HarnessError):
            prepare_contract(self.store, proposal, {'productId': 'p'})
        value = prepare_contract(self.store, proposal, {'productId': 'p'},
                                 pending_cycle=cycle, pending_quality=quality)
        self.assertEqual(value['workKind'], 'definition')
        with self.assertRaises(HarnessError):
            prepare_contract(self.store, proposal, {'productId': 'p'})
        self.assertEqual(cycle['protocolState'], 'validating')

    def test_exploration_does_not_read_product_descendant_evidence(self):
        target, _, _ = self.store.artifact('d1', 'direction', product='p', exploration='e')
        with self.assertRaisesRegex(HarnessError, 'OWNER_MISMATCH'):
            prepare_contract(self.store, self.proposal('review', [target]), {'explorationId': 'e'})

    def test_partial_handoff_is_readable_without_promoting_completed_artifact(self):
        target, cycle, submission = self.store.artifact('d1', 'definition')
        cycle.update(protocolState='validating', outcome='partial')
        submission['payload']['result'] = 'partial'
        value = prepare_contract(self.store, self.proposal('research', [target]), {'productId': 'p'},
                                 pending_cycle=cycle)
        self.assertEqual(value['inputRefs'], [target])
        with self.assertRaisesRegex(HarnessError, 'PREREQUISITE_MISSING'):
            prepare_contract(self.store, self.proposal('visual_exploration', [target]), {'productId': 'p'},
                             pending_cycle=cycle)
        cycle['outcome'] = 'failed'
        with self.assertRaisesRegex(HarnessError, 'CONTINUATION_BLOCKED'):
            prepare_contract(self.store, self.proposal('research', [target]), {'productId': 'p'},
                             pending_cycle=cycle)

    def test_changes_required_and_model_phase_review_never_grant_quality(self):
        definition, _, _ = self.store.artifact('d1', 'definition')
        review, cycle = self.store.reviewed(definition, ['visual_exploration'], verdict='changes_required')
        with self.assertRaisesRegex(HarnessError, 'REVIEW_REQUIRED'):
            prepare_contract(self.store, self.proposal('visual_exploration', [definition], [review]), {'productId': 'p'})
        cycle['qualityApplicability'] = []
        cycle['report'] = {'reportedPhase': 'review'}
        with self.assertRaisesRegex(HarnessError, 'REVIEW_REQUIRED'):
            prepare_contract(self.store, self.proposal('visual_exploration', [definition], [review]), {'productId': 'p'})


if __name__ == '__main__':
    unittest.main()
