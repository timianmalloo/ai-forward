"""Explicit pre-start scope decisions stay within the same owned task."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class PrestartScopeGuidanceTests(unittest.TestCase):
    def test_explicit_scope_change_has_bound_recovery_without_silent_weakening(self):
        reference=(ROOT/'pack/commands/deliver/reference/checkpoints.md').read_text(encoding='utf-8')
        skill=(ROOT/'pack/commands/deliver/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('--scope-change',reference)
        self.assertIn('before',reference)
        self.assertIn('after',reference)
        self.assertIn('original answer',reference)
        self.assertIn('explicitly',reference)
        self.assertIn('same task',skill)
        self.assertIn('scope-change',skill)
