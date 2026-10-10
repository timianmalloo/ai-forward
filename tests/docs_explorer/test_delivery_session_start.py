"""Installed lifecycle regressions through real hook and checkpoint subprocesses.
Bound review/permission receipts are synthetic fixtures, not authentic consent.
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

import test_delivery as fixtures
import test_delivery_checkpoint_guards as guards
from test_pack_apply import pa

ROOT = Path(__file__).resolve().parents[2]


class InstalledSessionResumeTests(unittest.TestCase):
    def test_fresh_session_runtime_marker_does_not_invalidate_reviewed_permission_pause(self):
        for plain in (False, True):
            with self.subTest(project='plain' if plain else 'git'):
                fixture = guards.DeliveryCheckpointGuardTests('runTest')
                fixture.setUp()
                try:
                    rows = pa.Applier(str(ROOT), str(fixture.repo), dry=False,
                                      install=True, baselines=False).run()
                    self.assertFalse([row for row in rows if row['status'] == 'fail'])
                    installed = fixture.repo / 'docs/ai-forward-pack'
                    def session_start(session_id):
                        result = subprocess.run(
                            [sys.executable, str(installed / 'hooks/session-start.py'), '--host', 'claude'],
                            input=json.dumps({'hook_event_name': 'SessionStart', 'session_id': session_id,
                                              'cwd': str(fixture.repo)}), cwd=fixture.repo,
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
                        self.assertEqual(0, result.returncode, result.stderr)

                    # Native hosts fire SessionStart before the task starts, then again
                    # when a new session resumes it. Include both real lifecycle calls.
                    session_start('initial-fixture')
                    with mock.patch.object(fixtures, 'SCRIPT', installed / 'scripts/delivery.py'):
                        app, _ = fixture.reviewed(tier='T1', plain=plain)
                        product = app.read_bytes()
                        proof = fixture.write('permission-proof.json', {'observed': 'paused fixture'})
                        paused = fixture.run_cli('pause', '--task', 'demo', '--kind', 'permission',
                                                 '--authority', 'human', '--question', 'Allow check?',
                                                 '--actor', 'author', '--evidence', proof)
                        receipt = fixture.receipt(paused)
                        session_start('fresh-fixture')
                        marker = fixture.repo / '.agents/log/audit/.run-starts.json'
                        self.assertTrue(marker.is_file(), 'The actual installed hook must write its fallback')
                        self.assertFalse((fixture.repo / 'docs/audit').exists(), 'Do not opt into product audit')
                        self.assertEqual(product, app.read_bytes())
                        resumed = fixture.run_cli('resume', '--task', 'demo', '--receipt', receipt)
                        self.assertEqual('verify', resumed['next'])
                finally:
                    fixture.doCleanups()

    def test_declared_startup_checks_run_without_waiving_reviewed_product_drift(self):
        for plain in (False, True):
            for modifies_product in (False, True):
                with self.subTest(project='plain' if plain else 'git', mutation=modifies_product):
                    fixture = guards.DeliveryCheckpointGuardTests('runTest')
                    fixture.setUp()
                    try:
                        rows = pa.Applier(str(ROOT), str(fixture.repo), dry=False,
                                          install=True, baselines=False).run()
                        self.assertFalse([row for row in rows if row['status'] == 'fail'])
                        installed = fixture.repo / 'docs/ai-forward-pack'
                        check = fixture.repo / 'startup_check.py'
                        check.write_text(
                            'from pathlib import Path\nimport sys\n'
                            'Path(sys.argv[1]).write_text("observed", encoding="utf-8")\n'
                            + ('Path("app.py").write_text("changed by declared check", encoding="utf-8")\n'
                               if modifies_product else ''), encoding='utf-8')
                        external = Path(fixture.tmp.name) / 'startup-observed.txt'
                        settings = fixture.repo / '.agents/session-checks.json'
                        settings.write_text(json.dumps({'checks': [{'name': 'declared check',
                            'argv': ['{python}', str(check), str(external)],
                            'remedy': 'Inspect the startup check result.'}]}), encoding='utf-8')
                        # Native hosts start once before the reviewed checkpoint.
                        # Include that seam so normal Python import caches predate review.
                        subprocess.run([sys.executable, str(installed / 'hooks/session-start.py'),
                            '--host', 'claude'], input=json.dumps({'hook_event_name': 'SessionStart',
                            'session_id': 'initial-declared-fixture', 'cwd': str(fixture.repo)}),
                            cwd=fixture.repo, capture_output=True, text=True, encoding='utf-8',
                            check=True, timeout=30)
                        with mock.patch.object(fixtures, 'SCRIPT', installed / 'scripts/delivery.py'):
                            fixture.reviewed(tier='T1', plain=plain)
                            proof = fixture.write('permission-proof.json', {'observed': 'paused fixture'})
                            paused = fixture.run_cli('pause', '--task', 'demo', '--kind', 'permission',
                                '--authority', 'human', '--question', 'Allow check?',
                                '--actor', 'author', '--evidence', proof)
                            receipt = fixture.receipt(paused)
                            result = subprocess.run([sys.executable, str(installed / 'hooks/session-start.py'),
                                '--host', 'claude'], input=json.dumps({'hook_event_name': 'SessionStart',
                                'session_id': 'declared-fixture', 'cwd': str(fixture.repo)}),
                                cwd=fixture.repo, capture_output=True, text=True, encoding='utf-8', timeout=30)
                            self.assertEqual(0, result.returncode, result.stderr)
                            self.assertEqual('observed', external.read_text(encoding='utf-8'))
                            if modifies_product:
                                failure = fixture.run_cli('resume', '--task', 'demo', '--receipt', receipt, ok=False)
                                self.assertIn('input drift:', failure.stderr)
                            else:
                                self.assertEqual('verify', fixture.run_cli('resume', '--task', 'demo',
                                    '--receipt', receipt)['next'])
                    finally:
                        fixture.doCleanups()

    def test_runtime_marker_exclusions_do_not_hide_durable_records_or_product_edits(self):
        for plain in (False, True):
            with self.subTest(project='plain' if plain else 'git'):
                fixture = guards.DeliveryCheckpointGuardTests('runTest')
                fixture.setUp()
                try:
                    rows = pa.Applier(str(ROOT), str(fixture.repo), dry=False,
                                      install=True, baselines=False).run()
                    self.assertFalse([row for row in rows if row['status'] == 'fail'])
                    installed = fixture.repo / 'docs/ai-forward-pack'
                    with mock.patch.object(fixtures, 'SCRIPT', installed / 'scripts/delivery.py'):
                        app, _ = fixture.reviewed(tier='T1', plain=plain)
                        for relative in ('docs/audit/.run-starts.json', 'docs/audit/.run-starts.json.tmp',
                                         '.agents/log/audit/.run-starts.json',
                                         '.agents/log/audit/.run-starts.json.tmp'):
                            marker = fixture.repo / relative
                            marker.parent.mkdir(parents=True, exist_ok=True)
                            marker.write_text('{"duration": "fixture"}\n', encoding='utf-8')
                        self.assertEqual('verify', fixture.run_cli('status', '--task', 'demo')['next'])
                        for relative in ('.agents/log/audit/audit-log.jsonl',
                                         '.agents/log/coordination.jsonl', 'docs/audit/product.json'):
                            record = fixture.repo / relative
                            record.write_text('{"record": "must remain visible"}\n', encoding='utf-8')
                            failure = fixture.run_cli('status', '--task', 'demo', ok=False)
                            self.assertIn('input drift:', failure.stderr)
                            record.unlink()
                        app.write_text('def value():\n    return 2\n', encoding='utf-8')
                        self.assertIn('input drift:', fixture.run_cli('status', '--task', 'demo', ok=False).stderr)
                finally:
                    fixture.doCleanups()

    def test_explicit_duration_marker_input_is_not_waived_in_a_plain_project(self):
        fixture = guards.DeliveryCheckpointGuardTests('runTest')
        fixture.setUp()
        try:
            rows = pa.Applier(str(ROOT), str(fixture.repo), dry=False,
                              install=True, baselines=False).run()
            self.assertFalse([row for row in rows if row['status'] == 'fail'])
            installed = fixture.repo / 'docs/ai-forward-pack'
            with mock.patch.object(fixtures, 'SCRIPT', installed / 'scripts/delivery.py'):
                fixture.reviewed(plain=True)
                marker = fixture.repo / '.agents/log/audit/.run-starts.json'
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.write_text('{"input": "original"}\n', encoding='utf-8')
                fixture.run_cli('start', '--task', 'explicit-input', '--facts', fixture.facts(),
                                '--audit-root', fixture.audit, '--compiled-id', fixture.compiled_id,
                                '--input', marker)
                fixture.run_cli('status', '--task', 'explicit-input')
                marker.write_text('{"input": "changed"}\n', encoding='utf-8')
                self.assertIn('input drift:', fixture.run_cli('status', '--task', 'explicit-input', ok=False).stderr)
        finally:
            fixture.doCleanups()

    def test_plain_runtime_marker_symlink_is_not_excluded(self):
        fixture = guards.DeliveryCheckpointGuardTests('runTest')
        fixture.setUp()
        try:
            rows = pa.Applier(str(ROOT), str(fixture.repo), dry=False,
                              install=True, baselines=False).run()
            self.assertFalse([row for row in rows if row['status'] == 'fail'])
            installed = fixture.repo / 'docs/ai-forward-pack'
            with mock.patch.object(fixtures, 'SCRIPT', installed / 'scripts/delivery.py'):
                app, _ = fixture.reviewed(plain=True)
                marker = fixture.repo / '.agents/log/audit/.run-starts.json'
                marker.parent.mkdir(parents=True, exist_ok=True)
                try:
                    marker.symlink_to(app)
                except OSError as error:
                    self.skipTest('Native symlink creation unavailable: ' + str(error))
                self.assertIn('input drift:', fixture.run_cli('status', '--task', 'demo', ok=False).stderr)
        finally:
            fixture.doCleanups()

    def test_source_repository_ignores_only_ephemeral_fallback_markers(self):
        for relative, expected in (('.agents/log/audit/.run-starts.json', 0),
                                   ('.agents/log/audit/.run-starts.json.tmp', 0),
                                   ('.agents/log/audit/audit-log.jsonl', 1),
                                   ('.agents/log/coordination.jsonl', 1)):
            with self.subTest(path=relative):
                result = subprocess.run(['git', 'check-ignore', '--quiet', '--no-index', relative],
                                        cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(expected, result.returncode, result.stderr)


if __name__ == '__main__':
    unittest.main()
