"""Explicit selectors, guarded I/O and the real attempt-bound socket."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/core'))
import company_harness_handoff as helper
from company_harness import HarnessStore
from company_harness_bridge import running_bridge
from company_harness_client import request, material
from project_isolation import IsolationError


@unittest.skipUnless(sys.platform == 'linux', 'Real Unix socket and safe file I/O')
class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='handoff-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('docs', 'logs', 'inputs'):
            (self.root / name).mkdir()
        self.primary = self.root / 'docs/result.md'
        self.primary.write_text('Actual bounded result')
        self.plan = {'contract': {'objective': 'Resolve one question', 'workKind': 'research',
                     'scope': ['One bounded question'], 'completionOrHandoff': 'A usable conclusion'},
                     'inputs': [], 'prerequisites': []}
        self.index = self.root / 'inputs'
        (self.index / 'index.json').write_text('[]')
        self.store = HarnessStore(self.root, create=True)
        self.store.create_cycle({'cycleId': 'cycle', 'productId': 'product', 'sequenceNumber': 1,
                                 'objective': 'One result', 'workKind': 'research', 'project': 'projects/owned'})
        self.context = self.store.begin_attempt('cycle', 'attempt', {'dispatchId': 'owned'})['context']
        self.socket = self.root / 'bridge.sock'
        self.enterContext(patch.dict(os.environ, AUTONOMOUS_COMPANY_ROOT=str(self.root),
            AUTONOMOUS_COMPANY_ATTEMPT_ID='attempt', COMPANY_HARNESS_SOCKET=str(self.socket),
            COMPANY_HARNESS_TOKEN='token', COMPANY_HARNESS_RECOVERY='0'))
        self.enterContext(running_bridge(self.socket, self.store, self.context, 'token'))

    def run_plan(self, plan=None, primary='docs/result.md', evidence=None):
        (self.root / 'logs/plan.json').write_text(json.dumps(plan or self.plan))
        return helper.generate('logs/plan.json', primary, evidence or [], input_directory=self.index)

    def output(self):
        return self.root / 'docs/harness/attempt-handoff.json'

    def add_input(self, name='history.md', data=b'old result', identity='old'):
        (self.index / name).write_bytes(data)
        entry = {'file': name, 'evidenceId': identity, 'sha256': hashlib.sha256(data).hexdigest(), 'mediaType': 'text/plain'}
        (self.index / 'index.json').write_text(json.dumps([entry]))
        return entry

    def test_deterministic_generation_and_submit_lost_ack(self):
        self.add_input()
        self.store.bind_evidence('cycle', 'old', 'old result')
        self.plan['inputs'] = [{'input': 'history.md'}, {'primary': True}]
        first = self.run_plan()
        raw = self.output().read_bytes()
        self.assertEqual(first, self.run_plan())
        self.assertEqual(raw, self.output().read_bytes())
        self.assertEqual(first['inputCount'], 2)
        primary, _ = material('docs/result.md')
        handoff, _ = material(first['handoffPath'])
        payload = {'result': 'completed', 'unfinishedItems': [], 'evidenceRefs': [primary, handoff],
                   'primaryEvidenceId': primary['evidenceId'], 'handoffRef': handoff}
        receipt = request('submit', 'same-id', payload)
        self.assertEqual(receipt['status'], 'accepted')
        with patch.object(helper, 'atomic_write') as writer, self.assertRaisesRegex(ValueError, 'ALREADY_ACCEPTED'):
            self.run_plan()
        writer.assert_not_called()
        self.assertEqual(raw, self.output().read_bytes())
        self.assertEqual(request('submit', 'same-id', payload), receipt)
        self.assertEqual(request('submit', 'same-id', {**payload, 'result': 'partial'})['errorCode'], 'ID_CONFLICT')
        self.assertEqual(request('submit', 'new-id', payload)['errorCode'], 'SUBMISSION_ALREADY_ACCEPTED')

    def test_status_mismatch_unavailable_and_fencing_write_nothing(self):
        for response in ({'status': 'rejected'}, {'cycle': None}, {}):
            with patch.object(helper, 'request', return_value=response), self.assertRaises(ValueError):
                self.run_plan()
        with patch.object(helper, 'request', side_effect=OSError('offline')), self.assertRaises(OSError):
            self.run_plan()
        with patch.dict(os.environ, AUTONOMOUS_COMPANY_ATTEMPT_ID='foreign'), self.assertRaises(ValueError):
            self.run_plan()
        self.store.claim_controller('new-controller')
        with self.assertRaises(ValueError):
            self.run_plan()
        self.assertFalse((self.root / 'docs/harness').exists())

    def test_bad_plan_and_selectors_preserve_existing_output(self):
        self.run_plan()
        original = self.output().read_bytes()
        variants = []
        for selector in ({'input': 'missing'}, {'evidence': 'docs/unlisted'}, {'primary': 1}, {'evidenceId': 'raw', 'sha256': '0' * 64}):
            value = deepcopy(self.plan)
            value['inputs'] = [selector]
            variants.append(value)
        for field, value in [('inputRefs', []), ('unknown', True), ('workKind', []), ('revisesKind', [])]:
            bad = deepcopy(self.plan)
            bad['contract'][field] = value
            if field == 'revisesKind':
                bad['contract']['workKind'] = 'revision'
            variants.append(bad)
        variants.append({**self.plan, 'extra': True})
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.run_plan(bad)
            self.assertEqual(self.output().read_bytes(), original)

    def test_scopes_symlinks_hardlinks_and_self_reference(self):
        (self.root / 'docs/link').symlink_to(self.primary)
        os.link(self.primary, self.root / 'docs/hard')
        for name in ('../outside', str(self.primary), 'docs/../logs/plan.json', '.claude/input',
                     'projects/foreign/file', 'docs/link', 'docs/hard', 'docs/harness/attempt-handoff.json'):
            with self.subTest(name=name), self.assertRaises((ValueError, OSError, IsolationError)):
                self.run_plan(primary=name)
        self.assertFalse(self.output().exists())

    def test_index_actual_hash_and_metadata(self):
        entry = self.add_input()
        self.plan['inputs'] = [{'input': 'history.md'}]
        for bad in ({**entry, 'sha256': '0' * 64}, {**entry, 'mediaType': ''}):
            (self.index / 'index.json').write_text(json.dumps([bad]))
            with self.assertRaises(ValueError):
                self.run_plan()
        (self.index / 'index.json').write_text(json.dumps([entry, entry]))
        with self.assertRaises(ValueError):
            self.run_plan()

    def test_material_changed_or_accepted_between_read_and_write(self):
        original = helper.active_status
        for mode in ('mutate', 'accepted'):
            calls = []
            def status(attempt):
                calls.append(attempt)
                if len(calls) == 2:
                    if mode == 'mutate':
                        self.primary.write_text('changed during generation')
                    else:
                        request('submit', 'stop', {'result': 'failed', 'unfinishedItems': []})
                return original(attempt)
            with patch.object(helper, 'active_status', side_effect=status), self.assertRaises(ValueError):
                self.run_plan()
            self.assertFalse(self.output().exists())

    def test_real_material_and_package_limits(self):
        self.primary.write_bytes(b'x' * helper.MATERIAL_LIMIT)
        self.run_plan()
        self.primary.write_bytes(b'x' * (helper.MATERIAL_LIMIT + 1))
        with self.assertRaises(ValueError):
            self.run_plan()
        self.primary.write_bytes(b'x' * helper.MATERIAL_LIMIT)
        entries = []
        for i in range(8):
            name = str(i) + '.txt'
            data = bytes([i]) * helper.MATERIAL_LIMIT
            entries.append(self.add_input(name, data, 'old-' + str(i)))
        (self.index / 'index.json').write_text(json.dumps(entries))
        self.plan['inputs'] = [{'input': x['file']} for x in entries[:7]]
        self.assertEqual(self.run_plan()['inputBytes'], helper.MAX_BYTES)
        self.plan['inputs'].append({'input': entries[7]['file']})
        with self.assertRaisesRegex(ValueError, 'bytes'):
            self.run_plan()
        refs = {str(i): {'evidenceId': str(i), 'sha256': str(i).zfill(64)} for i in range(17)}
        p = deepcopy(self.plan)
        p['inputs'] = [{'input': str(i)} for i in range(1, 16)]
        self.assertEqual(len(helper.compile_plan(p, refs['0'], refs, {})['nextContract']['inputRefs']), 16)
        p['inputs'].append({'input': '16'})
        with self.assertRaisesRegex(ValueError, 'count'):
            helper.compile_plan(p, refs['0'], refs, {})

    def test_conflicting_refs_and_current_review_prerequisite(self):
        primary, _ = material('docs/result.md')
        p = deepcopy(self.plan)
        p['prerequisites'] = [{'primary': True}]
        result = helper.compile_plan(p, primary, {}, {})['nextContract']
        self.assertEqual(result['inputRefs'], result['prerequisiteRefs'])
        p['inputs'] = [{'input': 'conflict'}]
        with self.assertRaisesRegex(ValueError, 'CONFLICTING'):
            helper.compile_plan(p, primary, {'conflict': {**primary, 'sha256': '0' * 64}}, {})

    def test_write_failure_does_not_replace_success_or_leave_temporary_file(self):
        self.run_plan()
        original = self.output().read_bytes()
        with patch('product_identity.os.replace', side_effect=OSError('injected')), self.assertRaises(OSError):
            self.run_plan()
        self.assertEqual(self.output().read_bytes(), original)
        self.assertEqual(list(self.output().parent.iterdir()), [self.output()])

    def test_recovery_output_envelope_limit_and_no_other_writes(self):
        status = request('status')
        status['attempt']['recoveryId'] = 'recovery'
        status.update(recovery=True)
        status['cycle']['protocolState'] = 'recovering'
        target = self.root / '.company-harness-protocol/attempt/handoff.json'
        target.parent.mkdir(parents=True)
        with patch.object(helper, 'request', return_value=status), patch.dict(os.environ, COMPANY_HARNESS_RECOVERY='1'):
            first = self.run_plan()
            self.assertEqual(first['handoffPath'], '.company-harness-protocol/attempt/handoff.json')
            overhead = len(target.read_bytes()) - len(self.plan['contract']['scope'][0].encode())
            self.plan['contract']['scope'] = ['x' * (16384 - overhead)]
            self.run_plan()
            self.assertEqual(target.stat().st_size, 16384)
            original = target.read_bytes()
            self.plan['contract']['scope'][0] += 'x'
            with self.assertRaisesRegex(ValueError, 'PROTOCOL_MATERIAL_TOO_LARGE'):
                self.run_plan()
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(target.parent.iterdir()), [target])
            self.assertFalse(self.output().exists())
            self.plan['contract']['scope'] = ['One bounded question']
            with patch.object(helper.os, 'fsync', side_effect=OSError('interrupted')), self.assertRaises(OSError):
                self.run_plan()

    def test_review_targets_selector_compiles_review_requirement_and_validates_kind(self):
        bg, _ = material('docs/result.md')
        entry = self.add_input('direction.md', b'Proposed product direction', 'dir-1')
        self.store.bind_evidence('cycle', 'dir-1', 'Proposed product direction')
        plan = {
            'contract': {
                'objective': 'Review proposed direction only',
                'workKind': 'review',
                'scope': ['review direction'],
                'completionOrHandoff': 'verdict',
            },
            'inputs': [{'primary': True}],
            'prerequisites': [],
            'reviewTargets': [{'input': 'direction.md'}],
        }
        res = self.run_plan(plan)
        compiled = json.loads(self.output().read_text())['nextContract']
        expected_target = {'evidenceId': entry['evidenceId'], 'sha256': entry['sha256']}
        expected_bg = {'evidenceId': bg['evidenceId'], 'sha256': bg['sha256']}
        self.assertEqual(compiled['reviewRequirement'], {'independent': True, 'targetRefs': [expected_target]})
        self.assertEqual(compiled['inputRefs'], [expected_bg, expected_target])
        self.assertEqual(res['inputCount'], 2)

        bad_kind = deepcopy(plan)
        bad_kind['contract']['workKind'] = 'research'
        with self.assertRaisesRegex(ValueError, 'reviewTargets'):
            self.run_plan(bad_kind)


if __name__ == '__main__':
    unittest.main()
