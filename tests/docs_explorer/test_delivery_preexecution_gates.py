"""A selected skill's plan veto must stop execution, not become a late review."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class PreexecutionGateGuidanceTests(unittest.TestCase):
    def test_selected_plan_gate_is_checkpointed_before_execution(self):
        text=(ROOT/'pack/commands/deliver/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('before the first product edit',text)
        self.assertIn('never defer it to the final review',text)
        self.assertIn('pause --kind hard-veto --authority reviewer',text)
        self.assertIn("a selected skill's existing plan is that plan",text)
    def test_prior_missed_gate_is_not_retroactive_clearance(self):
        text=(ROOT/'pack/commands/deliver/reference/checkpoints.md').read_text(encoding='utf-8')
        self.assertIn('A late approval does not prove a pre-execution gate occurred',text)
        self.assertIn('retain the missed-gate evidence',text)
if __name__=='__main__': unittest.main()
