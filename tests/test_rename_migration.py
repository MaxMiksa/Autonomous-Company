"""One-time rename contracts on real directories/SQLite, without any model."""
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('rename_migration', ROOT / 'scripts/migrate-name.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
sys.path.insert(0, str(ROOT / 'scripts/core'))
from namespace_guard import check_center, check_environment, check_root


class RenameMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.root = self.folder / 'runtime'
        self.root.mkdir()
        self.manifest = self.folder / 'migration.json'

    def write(self, relative, value):
        file = self.root / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(value if isinstance(value, bytes) else value.encode())
        return file

    def center(self):
        old = self.folder / 'AutoCompany/center'
        old.mkdir(parents=True)
        new = self.folder / 'AutonomousCompany/center'
        connection = sqlite3.connect(old / 'center.sqlite3')
        connection.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
        connection.executemany('INSERT INTO metadata VALUES (?,?)', [('centerId', 'center-original'), ('schemaVersion', '1'), ('revision', '42')])
        connection.execute('CREATE TABLE records (kind TEXT,id TEXT,body TEXT, PRIMARY KEY(kind,id))')
        connection.executemany('INSERT INTO records VALUES (?,?,?)', [
            ('controls', 'queue', json.dumps({'revision': 8, 'dispatchEnabled': True})),
            ('requests', 'original-request', json.dumps({'state': 'queued', 'startAuthorized': True, 'configFingerprint': 'original-config-hash'})),
            ('sources', 'original-source', json.dumps({'root': str(old / 'runtimes/original'), 'productId': 'original-product'})),
            ('events', 'original-event', json.dumps({'text': 'Auto Company historical fact', 'receipt': 'original-receipt'})),
        ])
        connection.commit()
        connection.close()
        (old / 'center.lock').write_bytes(b'0')
        (old / 'operator-note.txt').write_bytes(b'Original human note')
        return old, new

    def test_configuration_identity_and_history_round_trip(self):
        for version in ('1.6.0', '2.2.0'):
            with self.subTest(version=version):
                self.write('package.json', json.dumps({'version': version}))
                original = b'# human comment\r\nAUTO_COMPANY_LANGUAGE=en\r\nX_AUTO_COMPANY_SETTING=keep\r\nACTIVE_PROJECT=projects/one\r\n'
                self.write('.auto-company.local', original)
                (self.root / '.auto-company.local').chmod(0o600)
                self.write('.auto-company/product-state.json', '{"identity":"original", "cycle":17}')
                self.write('projects/one/.auto-company/identity.json', '{"id":"original-product"}')
                self.write('memories/consensus.md', '# Auto Company Consensus\n## Human Overrides\nDo not publish\n')
                before = M.tree(self.root)
                result = M.apply(self.manifest, [self.root])
                self.assertEqual(result['state'], 'complete')
                check_root(self.root)
                current = (self.root / '.autonomous-company.local').read_bytes()
                self.assertIn(b'AUTONOMOUS_COMPANY_LANGUAGE=en\r\n', current)
                self.assertIn(b'X_AUTO_COMPANY_SETTING=keep', current)
                if os.name != 'nt':
                    self.assertEqual((self.root / '.autonomous-company.local').stat().st_mode & 0o777, 0o600)
                self.assertEqual((self.root / '.autonomous-company/product-state.json').read_bytes(), b'{"identity":"original", "cycle":17}')
                self.assertEqual((self.root / 'memories/consensus.md').read_bytes(), b'# Auto Company Consensus\n## Human Overrides\nDo not publish\n')
                self.assertEqual(M.apply(self.manifest)['migrationId'], result['migrationId'])
                M.rollback(self.manifest)
                self.assertEqual(M.tree(self.root), before)
                self.manifest = self.folder / 'second-migration.json'

    def test_conflict_or_pending_governance_does_not_mutate_source(self):
        file = self.write('.auto-company.local', 'AUTO_COMPANY_LANGUAGE=en\n')
        self.write('.autonomous-company.local', 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n')
        before = M.tree(self.root)
        with self.assertRaisesRegex(ValueError, 'occupied'):
            M.apply(self.manifest, [self.root])
        self.assertEqual(M.tree(self.root), before)
        (self.root / '.autonomous-company.local').unlink()
        self.write('.auto-company/product-state.transaction.json', '{}')
        with self.assertRaisesRegex(ValueError, 'original writer'):
            M.prepare([self.root])
        self.assertEqual(file.read_bytes(), b'AUTO_COMPANY_LANGUAGE=en\n')

    def test_conflicting_environment_names_and_old_center_fail_before_creation(self):
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            M.config(b'AUTO_COMPANY_LANGUAGE=en\nAUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n')
        with self.assertRaisesRegex(ValueError, 'Legacy environment'):
            check_environment({'AUTO_COMPANY_LANGUAGE': 'en', 'AUTONOMOUS_COMPANY_LANGUAGE': 'zh-CN'})
        old, new = self.center()
        with self.assertRaisesRegex(ValueError, 'Old center data'):
            check_center(new)
        self.assertFalse(new.exists())

    def test_native_center_move_pauses_and_preserves_identity_and_receipts(self):
        old, new = self.center()
        before = M.tree(old)
        M.apply(self.manifest, data_dir=old, new_data_dir=new)
        self.assertFalse(old.exists())
        check_center(new)
        connection = sqlite3.connect(new / 'center.sqlite3')
        self.assertEqual(connection.execute("SELECT value FROM metadata WHERE key='centerId'").fetchone()[0], 'center-original')
        rows = {(kind, identity): json.loads(body) for kind, identity, body in connection.execute('SELECT kind,id,body FROM records')}
        connection.close()
        self.assertFalse(rows['controls', 'queue']['dispatchEnabled'])
        self.assertFalse(rows['requests', 'original-request']['startAuthorized'])
        self.assertEqual(rows['requests', 'original-request']['configFingerprint'], 'original-config-hash')
        self.assertEqual(rows['events', 'original-event']['receipt'], 'original-receipt')
        self.assertEqual(rows['sources', 'original-source']['root'], str(new / 'runtimes/original'))
        M.rollback(self.manifest)
        self.assertEqual(M.tree(old), before)

    def test_namespace_rename_interruption_resumes(self):
        self.write('.auto-company.local', 'AUTO_COMPANY_LANGUAGE=en\n')
        replace = M.os.replace
        def interrupt(source, target):
            replace(source, target)
            if Path(source).name == '.auto-company.local':
                raise InterruptedError('injected after directory entry rename')
        with mock.patch.object(M.os, 'replace', side_effect=interrupt):
            with self.assertRaises(InterruptedError):
                M.apply(self.manifest, [self.root])
        with self.assertRaisesRegex(ValueError, 'in progress'):
            check_root(self.root)
        self.assertEqual(M.apply(self.manifest)['state'], 'complete')
        self.assertEqual((self.root / '.autonomous-company.local').read_text(), 'AUTONOMOUS_COMPANY_LANGUAGE=en\n')

    def test_center_interruption_before_database_replace_resumes(self):
        old, new = self.center()
        atomic = M.atomic
        def interrupt(path, data):
            if Path(path) == new / 'center.sqlite3':
                raise InterruptedError('injected center cutover')
            return atomic(path, data)
        with mock.patch.object(M, 'atomic', side_effect=interrupt):
            with self.assertRaises(InterruptedError):
                M.apply(self.manifest, data_dir=old, new_data_dir=new)
        with self.assertRaisesRegex(ValueError, 'in progress'):
            check_center(new)
        self.assertEqual(M.apply(self.manifest)['state'], 'complete')
        M.rollback(self.manifest)
        self.assertTrue(old.is_dir())

    def test_busy_center_and_unresolved_dispatch_are_refused(self):
        old, new = self.center()
        with M.center_lock(old):
            command = [sys.executable, str(ROOT / 'scripts/migrate-name.py'), 'plan', '--data-dir', str(old), '--new-data-dir', str(new)]
            result = subprocess.run(command, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        connection = sqlite3.connect(old / 'center.sqlite3')
        connection.execute("UPDATE records SET body=? WHERE kind='requests'", (json.dumps({'state': 'attention', 'dispatchId': 'original-dispatch'}),))
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(ValueError, 'Reconcile'):
            M.prepare([], old, new)
        self.assertFalse(new.exists())

    def test_rollback_rejects_new_writers_and_new_content(self):
        self.write('.auto-company.local', 'AUTO_COMPANY_LANGUAGE=en\n')
        M.apply(self.manifest, [self.root])
        team = self.write('.autonomous-company.local.team-active', 'original team')
        with self.assertRaisesRegex(ValueError, 'original writer'):
            M.rollback(self.manifest)
        team.unlink()
        self.write('.autonomous-company.local', 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n')
        with self.assertRaisesRegex(ValueError, 'New content'):
            M.rollback(self.manifest)
        self.assertEqual((self.root / '.autonomous-company.local').read_text(), 'AUTONOMOUS_COMPANY_LANGUAGE=zh-CN\n')


if __name__ == '__main__':
    unittest.main()
