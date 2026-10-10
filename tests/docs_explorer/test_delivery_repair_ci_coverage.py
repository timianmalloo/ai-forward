"""Published native qualification must exercise the maintained outcome repairs."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class DeliveryRepairCICoverageTests(unittest.TestCase):
    def test_native_matrix_retains_old_checks_and_runs_outcome_repairs(self):
        text=(ROOT/'.github/workflows/adoption-entrypoints.yml').read_text(encoding='utf-8')
        for name in ('test_delivery_outcome_repairs.py', 'test_delivery_startup_composition.py',
                     'test_delivery_recovery_guidance.py', 'test_pack_doctor.py', 'test_run_evals.py',
                     'test_cross_platform_controls.py', 'test_coord_enforcement.py',
                     'test_coord_install_path.py', 'test_copilot_runner.py',
                     'test_prestart_scope_guidance.py', 'test_delivery_preexecution_gates.py'):
            with self.subTest(test=name): self.assertIn('tests/docs_explorer/'+name, text)
        self.assertIn('os: [ubuntu-latest, macos-latest, windows-latest]', text)
        self.assertIn('shell: cmd', text)
        self.assertIn('contents: read', text)
        self.assertNotIn('pull_request:', text)
