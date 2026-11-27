"""Quality bindings and dispatch prerequisites, without invoking a model."""
import copy
import base64
import hashlib
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
        content = 'Actual material ' + identity
        ref = {'evidenceId': identity + '-doc', 'sha256': hashlib.sha256(content.encode()).hexdigest()}
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
                                           'source': {'attemptId': attempt}, 'content': content, 'mediaType': 'text/plain'}
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

    def package_refs(self, count, size=20):
        refs = []
        for number in range(count):
            ref, _, _ = self.store.artifact('input-' + str(number), 'research')
            data = bytes([number]) * size
            ref['sha256'] = hashlib.sha256(data).hexdigest()
            self.store.evidence[ref['evidenceId']].update(sha256=ref['sha256'], content=base64.b64encode(data).decode(),
                                                       contentEncoding='base64', mediaType='application/octet-stream')
            refs.append(ref)
        return refs

    def test_input_package_capacity_is_rejected_at_contract_admission(self):
        for count, size in ((17, 1), (9, 1024 * 1024)):
            with self.subTest(count=count, size=size):
                self.store = MemoryEvidence()
                refs = self.package_refs(count, size)
                with self.assertRaisesRegex(HarnessError, 'INPUT_PACKAGE_INVALID'):
                    prepare_contract(self.store, self.proposal('review', refs), {'productId': 'p'})

    def test_input_package_exact_limits_deduplicate_both_reference_arrays(self):
        for count, size in ((16, 1), (8, 1024 * 1024)):
            with self.subTest(count=count, size=size):
                self.store = MemoryEvidence()
                refs = self.package_refs(count, size)
                contract = prepare_contract(self.store, self.proposal('review', refs + refs, refs), {'productId': 'p'})
                self.assertEqual(contract['inputRefs'], refs + refs)

    def test_input_package_rejects_invalid_decoding_and_actual_byte_hash(self):
        refs = self.package_refs(1)
        evidence = self.store.evidence[refs[0]['evidenceId']]
        for update in ({'content': 'not base64!'}, {'content': base64.b64encode(b'other bytes').decode()},
                       {'contentEncoding': 'unknown'}):
            with self.subTest(update=update):
                original = copy.deepcopy(evidence)
                evidence.update(update)
                with self.assertRaisesRegex(HarnessError, 'INPUT_PACKAGE_INVALID'):
                    prepare_contract(self.store, self.proposal('review', refs), {'productId': 'p'})
                evidence.clear()
                evidence.update(original)

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

    def test_latest_blocking_review_supersedes_prior_pass_for_same_version(self):
        definition, _, _ = self.store.artifact('d1', 'definition')
        passed, _ = self.store.reviewed(definition, ['visual_exploration'])
        _, blocked = self.store.reviewed(definition, ['visual_exploration'], verdict='changes_required')
        blocked['submissions'][0]['payload']['review']['issues'] = [{'blocking': True, 'message': 'Core journey missing'}]
        blocked['qualityApplicability'] = close_review(self.store, blocked, blocked['submissions'][0])
        with self.assertRaisesRegex(HarnessError, 'REVIEW_REQUIRED'):
            prepare_contract(self.store, self.proposal('visual_exploration', [definition], [passed]), {'productId': 'p'})

    def test_later_independent_pass_can_resolve_block_but_needs_current_reference(self):
        definition, _, _ = self.store.artifact('d1', 'definition')
        old, _ = self.store.reviewed(definition, ['visual_exploration'])
        self.store.reviewed(definition, ['visual_exploration'], verdict='changes_required')
        current, _ = self.store.reviewed(definition, ['visual_exploration'])
        with self.assertRaisesRegex(HarnessError, 'REVIEW_REQUIRED'):
            prepare_contract(self.store, self.proposal('visual_exploration', [definition], [old]), {'productId': 'p'})
        value = prepare_contract(self.store, self.proposal('visual_exploration', [definition], [current]), {'productId': 'p'})
        self.assertEqual(value['workKind'], 'visual_exploration')

    def test_later_review_for_other_work_kind_does_not_revoke_current_scope(self):
        definition, _, _ = self.store.artifact('d1', 'definition')
        passed, _ = self.store.reviewed(definition, ['visual_exploration'])
        self.store.reviewed(definition, ['implementation'], verdict='changes_required')
        value = prepare_contract(self.store, self.proposal('visual_exploration', [definition], [passed]), {'productId': 'p'})
        self.assertEqual(value['workKind'], 'visual_exploration')

    def test_progression_state_tracks_milestones_and_stagnation_levels(self):
        from company_harness_quality import progression_state
        identity = {'productId': 'p'}
        self.assertEqual(progression_state(self.store, identity)['stagnationLevel'], 'none')
        for idx in range(3):
            self.store.artifact(f'res-{idx}', 'research')
        warn = progression_state(self.store, identity)
        self.assertEqual(warn['stagnationLevel'], 'warning')
        self.assertEqual(warn['consecutiveNonAdvancing'], 3)
        self.assertEqual(warn['consecutiveSameWorkKind'], {'workKind': 'research', 'count': 3})
        self.assertIn('no direction head', warn['advisory'])

        for idx in range(3, 5):
            self.store.artifact(f'res-{idx}', 'research')
        crit = progression_state(self.store, identity)
        self.assertEqual(crit['stagnationLevel'], 'critical')
        self.assertEqual(crit['cyclesSinceLastMilestone'], 5)

        direction, _, _ = self.store.artifact('dir-1', 'direction')
        after_dir = progression_state(self.store, identity)
        self.assertEqual(after_dir['highestMilestone'], 'direction')
        self.assertEqual(after_dir['nextMilestone'], 'definition')
        self.assertEqual(after_dir['consecutiveNonAdvancing'], 0)
        self.assertEqual(after_dir['stagnationLevel'], 'none')

        for idx in range(3):
            self.store.artifact(f'val-{idx}', 'validation')
        need_rev = progression_state(self.store, identity)
        self.assertEqual(need_rev['stagnationLevel'], 'warning')
        self.assertIn('workKind=review', need_rev['advisory'])

        self.store.reviewed(direction, ['definition'])
        after_rev = progression_state(self.store, identity)
        self.assertEqual(after_rev['consecutiveNonAdvancing'], 0)
        self.assertEqual(after_rev['cyclesSinceLastMilestone'], 4)
        self.assertEqual(after_rev['stagnationLevel'], 'warning')
        self.assertIn('workKind=definition directly', after_rev['advisory'])

    def test_spin_guard_rejects_back_to_back_completed_objective_selection(self):
        identity = {'productId': 'p'}
        self.store.artifact('obj-1', 'objective')
        self.store.cycles[-1]['contract']['workKind'] = 'objective_selection'
        self.store.cycles[-1]['workKind'] = 'objective_selection'
        with self.assertRaisesRegex(HarnessError, 'SPIN_GUARD'):
            prepare_contract(self.store, self.proposal('objective_selection'), identity)
        self.assertEqual(prepare_contract(self.store, self.proposal('research'), identity)['workKind'], 'research')
        self.assertEqual(prepare_contract(self.store, self.proposal('direction'), identity)['workKind'], 'direction')
        self.store.cycles[-1]['outcome'] = 'partial'
        self.assertEqual(prepare_contract(self.store, self.proposal('objective_selection'), identity)['workKind'], 'objective_selection')

    def test_spin_guard_rejects_review_on_review_and_redundant_passed_reviews(self):
        identity = {'productId': 'p'}
        res, _, _ = self.store.artifact('res-1', 'research')
        rev, _ = self.store.reviewed(res, ['direction'])
        with self.assertRaisesRegex(HarnessError, 'SPIN_GUARD'):
            prepare_contract(self.store, self.proposal('review', [rev]), identity)
        with self.assertRaisesRegex(HarnessError, 'REDUNDANT_REVIEW'):
            prepare_contract(self.store, self.proposal('review', [res]), identity)

        d1, _, _ = self.store.artifact('dir-1', 'direction')
        self.store.reviewed(d1, ['definition'])
        # Missing 'experience' consumer approval, so reviewing d1 again is still allowed.
        self.assertEqual(prepare_contract(self.store, self.proposal('review', [d1]), identity)['workKind'], 'review')
        self.store.reviewed(d1, ['definition', 'experience'])
        with self.assertRaisesRegex(HarnessError, 'REDUNDANT_REVIEW'):
            prepare_contract(self.store, self.proposal('review', [d1]), identity)

        # Superseded by changes_required or producing a new head re-enables review.
        self.store.reviewed(d1, ['definition'], verdict='changes_required')
        self.assertEqual(prepare_contract(self.store, self.proposal('review', [d1]), identity)['workKind'], 'review')
        d2, _, _ = self.store.artifact('dir-2', 'direction')
        self.assertEqual(prepare_contract(self.store, self.proposal('review', [d2]), identity)['workKind'], 'review')

    def test_decoupled_review_target_refs_allows_background_inputs(self):
        identity = {'productId': 'p'}
        bg, _, _ = self.store.artifact('bg-1', 'research')
        target, _, _ = self.store.artifact('d-1', 'direction')
        outside, _, _ = self.store.artifact('other-1', 'research')
        with self.assertRaisesRegex(HarnessError, 'INVALID_FIELD'):
            prepare_contract(
                self.store,
                self.proposal('review', [bg, target], reviewRequirement={'targetRefs': [outside]}),
                identity,
            )
        contract = prepare_contract(
            self.store,
            self.proposal('review', [bg, target], reviewRequirement={'targetRefs': [target]}),
            identity,
        )
        self.assertEqual(contract['inputRefs'], [bg, target])
        self.assertEqual(contract['reviewRequirement'], {'independent': True, 'targetRefs': [target]})

        rev_doc, rev_cycle, submission = self.store.artifact('rev-1', 'review')
        rev_cycle['contract'].update(contract)
        submission['payload']['review'] = {
            'targetRefs': [bg, target],
            'verdict': 'passed',
            'issues': [],
            'qualityApplicability': ['definition'],
        }
        with self.assertRaisesRegex(HarnessError, 'INVALID_REVIEW'):
            close_review(self.store, rev_cycle, submission)
        submission['payload']['review']['targetRefs'] = [target]
        quality = close_review(self.store, rev_cycle, submission)
        self.assertEqual(len(quality), 1)
        self.assertEqual(quality[0]['targetRef'], target)
        self.assertEqual(quality[0]['artifactKind'], 'direction')


if __name__ == '__main__':
    unittest.main()
