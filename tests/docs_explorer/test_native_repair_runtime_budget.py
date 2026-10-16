"""Native repair qualification retains every check with sufficient time."""
from pathlib import Path
import unittest
class NativeBudget(unittest.TestCase):
    def test_full_windows_inventory_has_a_bounded_45_minute_job(self):
        text=(Path(__file__).resolve().parents[2]/'.github/workflows/adoption-entrypoints.yml').read_text()
        self.assertIn('timeout-minutes: 45',text)
        self.assertIn('test_delivery_outcome_repairs.py',text)
        self.assertIn('test_copilot_runner.py',text)
        self.assertIn('Exact one-liner under Windows cmd',text)
if __name__=='__main__':unittest.main()
